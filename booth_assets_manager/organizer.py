#!/usr/bin/env python3
import argparse
import csv
import json
import os
import re
import requests
import sys
from bs4 import BeautifulSoup
from .database import Database
from .settings import settings
from .vcc_integration import package_item, generate_repository_index

# Global constants
BASE_DIR = "BoothItems"

def sanitize_filename(name):
    """Sanitize a string to be used as a safe filename."""
    return re.sub(r'[\\/*?:"<>|]', "", name.replace(" ", "_"))

def extract_item_id(url):
    """Extracts the item ID from a Booth URL (handles both /items/<id> and /en/items/<id> patterns)."""
    match = re.search(r'/(?:en/)?items/(\d+)', url)
    return match.group(1) if match else "UnknownID"

def scrape_metadata(url):
    """
    Scrapes metadata from a Booth item URL.
    Adjust the CSS selectors if Booth's page structure changes.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to load page: {url} (Status code: {response.status_code})")
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Get title from meta tags first, then try page content
    title_el = soup.select_one("meta[property='og:title']") or \
               soup.select_one("title")
    if title_el:
        title = title_el.get("content", "") or title_el.get_text(strip=True)
        # Remove " - BOOTH" suffix if present
        title = title.replace(" - BOOTH", "").strip()
    else:
        title = "Untitled"

    # Get description from meta tags first, then try page content
    desc_el = soup.select_one("meta[property='og:description']") or \
              soup.select_one("div.js-market-item-detail-description p.autolink")
    description = desc_el.get("content", "") if desc_el else ""
    
    # Get images from meta tags and page content
    image_elements = []
    
    # Try meta image first
    meta_image = soup.select_one("meta[property='og:image']")
    if meta_image and meta_image.get("content"):
        image_elements.append({"src": meta_image.get("content")})
    
    # Then try page images
    content_images = soup.select("div.market-item-detail-item-image-wrapper img.market-item-detail-item-image")
    image_elements.extend(content_images)
    images = []
    for img in image_elements:
        src = img.get("src")
        if src:
            images.append(src)
    
    metadata = {
        "url": url,
        "item_id": extract_item_id(url),
        "title": title,
        "description": description,
        "images": images  # original image URLs from the page
    }
    return metadata

def download_images(metadata, folder_path, force_update=False):
    """
    Downloads images from the metadata's "images" list into an "images" subfolder
    within the item folder. Updates metadata with local paths.
    """
    images_dir = os.path.join(folder_path, "images")
    os.makedirs(images_dir, exist_ok=True)
    local_image_paths = []
    for i, img_url in enumerate(metadata.get("images", [])):
        # Determine file extension from URL; default to .jpg if none found.
        ext = os.path.splitext(img_url)[1]
        if not ext or len(ext) > 5:
            ext = ".jpg"
        filename = f"image_{i+1}{ext}"
        local_path = os.path.join(images_dir, filename)
        # If not forced and file exists, skip download.
        if not force_update and os.path.exists(local_path):
            local_image_paths.append(local_path)
            continue
        try:
            print(f"Downloading image {img_url}...")
            r = requests.get(img_url)
            if r.status_code == 200:
                with open(local_path, "wb") as f:
                    f.write(r.content)
                local_image_paths.append(local_path)
            else:
                print(f"Failed to download image: {img_url} (status {r.status_code})")
        except Exception as e:
            print(f"Error downloading image {img_url}: {e}")
    metadata["local_images"] = local_image_paths
    return metadata

def ensure_item_folder(metadata, force_update=False):
    """
    Ensures that a folder exists for the given item.
    If the metadata.json file is missing or force_update is True,
    it scrapes the item page to get fresh metadata and downloads images.
    Returns a tuple: (metadata, folder_path).
    """
    # First, get the item ID from the URL
    item_id = extract_item_id(metadata["url"])
    # Use a temporary title if not provided
    title = metadata.get("title", "Untitled")
    
    folder_name = f"{item_id}_{sanitize_filename(title)}"
    folder_path = os.path.join(BASE_DIR, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    meta_file = os.path.join(folder_path, "metadata.json")
    
    if force_update or not os.path.exists(meta_file):
        print(f"Scraping metadata for item {item_id}...")
        try:
            new_metadata = scrape_metadata(metadata["url"])
            # Download images as part of the metadata
            new_metadata = download_images(new_metadata, folder_path, force_update=force_update)
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(new_metadata, f, indent=4, ensure_ascii=False, sort_keys=True)
            return new_metadata, folder_path
        except Exception as e:
            print(f"Error scraping metadata for {metadata['url']}: {e}")
            return metadata, folder_path
    else:
        # Load existing metadata from the file.
        with open(meta_file, "r", encoding="utf-8") as f:
            existing_metadata = json.load(f)
        # If images haven't been downloaded yet, download them.
        if force_update or "local_images" not in existing_metadata:
            existing_metadata = download_images(existing_metadata, folder_path, force_update=force_update)
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(existing_metadata, f, indent=2, ensure_ascii=False)
        return existing_metadata, folder_path

def parse_input_file(file_path):
    """
    Reads the given input file and returns a list of items.
    Each item is a dict with at least a 'url' key.
    The file can be:
      - A CSV (with 'URL' or 'ID' columns; headers are case-insensitive)
      - A JSON file containing a list of objects
      - A plain text file (one entry per line)
    """
    items = []
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext == ".csv":
        with open(file_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            if not reader.fieldnames:
                print("CSV file appears to be empty.")
                return items
            for row in reader:
                # Convert all keys to lower-case for case-insensitivity
                row_lower = {key.lower(): value for key, value in row.items()}
                url = row_lower.get("url", "").strip()
                item_id = row_lower.get("id", "").strip()
                title = row_lower.get("title", "").strip()
                if url:
                    items.append({"url": url, "title": title})
                elif item_id:
                    constructed_url = f"https://booth.pm/items/{item_id}"
                    items.append({"url": constructed_url, "title": title})
                else:
                    print("Skipping row, no URL or ID found.")
    elif ext == ".json":
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                json_data = json.load(f)
                if isinstance(json_data, list):
                    for obj in json_data:
                        # Convert keys to lower-case for case-insensitivity
                        obj_lower = {key.lower(): value for key, value in obj.items()}
                        url = obj_lower.get("url", "").strip()
                        item_id = str(obj_lower.get("id", "")).strip()
                        title = obj_lower.get("title", "").strip()
                        if url:
                            items.append({"url": url, "title": title})
                        elif item_id:
                            constructed_url = f"https://booth.pm/items/{item_id}"
                            items.append({"url": constructed_url, "title": title})
                        else:
                            print("Skipping object, no URL or ID found.")
                else:
                    print("JSON file is not a list, expecting a list of objects.")
            except Exception as e:
                print(f"Error reading JSON file: {e}")
    else:
        # Assume plain text file: one URL or item ID per line.
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.lower().startswith("http"):
                    items.append({"url": line, "title": ""})
                else:
                    constructed_url = f"https://booth.pm/items/{line}"
                    items.append({"url": constructed_url, "title": ""})
    return items

def add_items(input_file, force_update):
    """Imports items from the input file, scrapes metadata, downloads images, and updates the database.
    If VCC integration is enabled and auto-package is enabled, also creates packages for new items.
    """
    items = parse_input_file(input_file)
    if not items:
        print("No valid items found in input file.")
        return
    
    db = Database()
    os.makedirs(BASE_DIR, exist_ok=True)
    
    for item in items:
        try:
            metadata, folder_path = ensure_item_folder(item, force_update=force_update)
            # Prepare image data as tuples of (url, local_path)
            images = list(zip(metadata["images"], metadata.get("local_images", [])))
            
            # Add to database
            db.add_item(
                item_id=metadata["item_id"],
                title=metadata["title"],
                url=metadata["url"],
                description=metadata.get("description", ""),
                folder_path=folder_path,
                images=images
            )
            print(f"Added/updated item {metadata['item_id']} in database.")
            
            # Create VCC package if enabled
            if settings.is_vcc_enabled() and settings.get_auto_package_new_items():
                try:
                    if package_item(metadata, settings.get_repository_path(), db):
                        print(f"Created VCC package for item {metadata['item_id']}.")
                except Exception as e:
                    print(f"Failed to create VCC package for item {metadata['item_id']}: {e}")
        except Exception as e:
            print(f"Failed to process item {item.get('url')}: {e}")
    
    # Regenerate repository index if VCC integration is enabled and any items were added
    if settings.is_vcc_enabled() and settings.get_auto_package_new_items() and len(items) > 0:
        try:
            generate_repository_index(
                settings.get_repository_path(),
                settings.get_repository_name(),
                settings.get_repository_id(),
                settings.get_repository_author()
            )
        except Exception as e:
            print(f"Failed to regenerate repository index: {e}")
    
    print("Items have been added/updated in the database.")

def remove_items(input_file, delete_folders):
    """Removes items (and optionally their folders) from the database based on the input file."""
    items = parse_input_file(input_file)
    if not items:
        print("No valid items found in input file.")
        return
    
    db = Database()
    removed_count = 0
    
    for item in items:
        item_id = extract_item_id(item["url"])
        # Get item data before removal to access folder path
        item_data = db.get_item(item_id)
        
        if item_data:
            if delete_folders and item_data["folder"] and os.path.exists(item_data["folder"]):
                try:
                    import shutil
                    shutil.rmtree(item_data["folder"])
                    print(f"Deleted folder: {item_data['folder']}")
                except Exception as e:
                    print(f"Failed to delete folder {item_data['folder']}: {e}")
            
            if db.remove_item(item_id):
                removed_count += 1
                print(f"Removed item {item_id} from database.")
        else:
            print(f"Item {item_id} not found in database.")
    
    print(f"Total items removed: {removed_count}")

def main():
    parser = argparse.ArgumentParser(
        description="Manage Booth items from a CSV, JSON, or plain text file. "
                    "Import or remove items from the local database."
    )
    parser.add_argument("input_file", help="Path to input file (CSV with 'URL'/'ID', JSON list, or plain text with one entry per line)")
    parser.add_argument("--force", action="store_true", help="Force re-download of metadata and images even if already present")
    parser.add_argument("--remove", action="store_true", help="Remove items from the database instead of adding")
    parser.add_argument("--delete-folders", action="store_true", help="(With --remove) Also delete the item folders from disk")
    # VCC integration options
    vcc_group = parser.add_argument_group('VCC Integration')
    vcc_group.add_argument("--vcc-enable", action="store_true", help="Enable VCC integration")
    vcc_group.add_argument("--vcc-disable", action="store_true", help="Disable VCC integration")
    vcc_group.add_argument("--vcc-status", action="store_true", help="Show VCC integration status")
    vcc_group.add_argument("--vcc-package", metavar="ITEM_ID", help="Package a specific item for VCC")
    vcc_group.add_argument("--vcc-package-all", action="store_true", help="Package all items for VCC")
    vcc_group.add_argument("--vcc-add", action="store_true", help="Add repository to VCC")
    
    args = parser.parse_args()

    # Handle VCC integration commands
    if args.vcc_enable:
        settings.set_vcc_enabled(True)
        settings.ensure_repository_structure()
        print("VCC integration enabled.")
        return
    
    if args.vcc_disable:
        settings.set_vcc_enabled(False)
        print("VCC integration disabled.")
        return
    
    if args.vcc_status:
        from .vcc_integration import test_vcc_integration
        
        if not settings.is_vcc_enabled():
            print("VCC integration is not enabled. Use --vcc-enable to enable it.")
            return
        
        status = test_vcc_integration(settings.get_repository_path())
        print(f"Repository Path: {settings.get_repository_path()}")
        print(f"Repository Exists: {'Yes' if status['repository_exists'] else 'No'}")
        print(f"Index Valid: {'Yes' if status['index_valid'] else 'No'}")
        print(f"Packages Found: {status['packages_found']}")
        print(f"VCC Protocol Works: {'Yes' if status['vcc_protocol_works'] else 'No'}")
        print(f"Overall Status: {status['overall_status']}")
        return
    
    if args.vcc_package:
        if not settings.is_vcc_enabled():
            print("VCC integration is not enabled. Use --vcc-enable to enable it.")
            return
        
        db = Database()
        item = db.get_item(args.vcc_package)
        if not item:
            print(f"Item {args.vcc_package} not found in database.")
            return
        
        if package_item(item, settings.get_repository_path(), db):
            print(f"Item {args.vcc_package} packaged successfully.")
        else:
            print(f"Failed to package item {args.vcc_package}.")
        return
    
    if args.vcc_package_all:
        if not settings.is_vcc_enabled():
            print("VCC integration is not enabled. Use --vcc-enable to enable it.")
            return
        
        from .vcc_integration import package_all_items
        db = Database()
        count = package_all_items(settings.get_repository_path(), db)
        print(f"Packaged {count} items.")
        return
    
    if args.vcc_add:
        if not settings.is_vcc_enabled():
            print("VCC integration is not enabled. Use --vcc-enable to enable it.")
            return
        
        from .vcc_integration import open_vcc_integration
        if open_vcc_integration(settings.get_repository_path()):
            print("VCC integration link opened in browser.")
        else:
            print("Failed to open VCC integration link. Please add the repository manually.")
            print(f"Repository path: file:///{os.path.abspath(os.path.join(settings.get_repository_path(), 'index.json')).replace(os.sep, '/')}")
        return

    # Handle regular commands
    if args.remove:
        remove_items(args.input_file, args.delete_folders)
    else:
        add_items(args.input_file, args.force)

if __name__ == "__main__":
    main()
