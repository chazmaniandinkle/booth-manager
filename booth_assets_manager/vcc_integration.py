#!/usr/bin/env python3
import os
import re
import json
import shutil
import urllib.parse
import platform
import subprocess
from datetime import datetime

def sanitize_id(text):
    """Convert text to a valid package ID component."""
    if not text:
        return "unknown"
    
    # Remove non-alphanumeric chars, replace spaces with dots
    sanitized = re.sub(r'[^a-zA-Z0-9]', '', text.replace(' ', '.'))
    
    # Ensure it starts with a letter
    if not sanitized or not sanitized[0].isalpha():
        sanitized = 'a' + sanitized
    
    return sanitized.lower()

def generate_package_id(item):
    """Generate a unique package ID for a Booth item."""
    # Extract creator name from the URL or use a default
    creator = "booth"  # Default
    if "creator" in item:
        creator = sanitize_id(item["creator"])
    
    # Use the item ID and sanitized title
    item_id = item["item_id"]
    title = sanitize_id(item.get("title", "item"))
    
    return f"com.{creator}.{title}.{item_id}"

def create_package_manifest(item, version="1.0.0"):
    """Create a package.json manifest from Booth item metadata."""
    package_id = generate_package_id(item)
    
    # Extract creator info
    creator_name = item.get("creator", "Booth Creator")
    creator_url = item.get("creator_url", "")
    
    # Create the manifest
    manifest = {
        "name": package_id,
        "displayName": item.get("title", "Booth Item"),
        "version": version,
        "unity": "2019.4",
        "description": item.get("description", "").strip()[:500],  # Limit description length
        "author": {
            "name": creator_name,
            "url": creator_url
        },
        "vpmDependencies": {},  # No dependencies for basic assets
        "url": f"file:///{os.path.abspath(item['folder']).replace(os.sep, '/')}",
        "legacyFolders": {},
        "legacyFiles": {}
    }
    
    return manifest

def create_package_structure(item, repository_path):
    """Create a Unity package structure for a Booth item."""
    # Generate package ID
    package_id = generate_package_id(item)
    
    # Create package directory
    package_dir = os.path.join(repository_path, "Packages", package_id)
    os.makedirs(package_dir, exist_ok=True)
    
    # Create standard folders
    runtime_dir = os.path.join(package_dir, "Runtime")
    docs_dir = os.path.join(package_dir, "Documentation~")
    os.makedirs(runtime_dir, exist_ok=True)
    os.makedirs(docs_dir, exist_ok=True)
    
    # Copy assets to Runtime folder
    item_folder = item["folder"]
    for root, dirs, files in os.walk(item_folder):
        # Skip the images folder and metadata.json
        if os.path.basename(root) == "images" or root == item_folder:
            continue
            
        # Create corresponding directory in Runtime
        rel_path = os.path.relpath(root, item_folder)
        target_dir = os.path.join(runtime_dir, rel_path)
        os.makedirs(target_dir, exist_ok=True)
        
        # Copy files
        for file in files:
            if file != "metadata.json":
                src_file = os.path.join(root, file)
                dst_file = os.path.join(target_dir, file)
                shutil.copy2(src_file, dst_file)
    
    # Copy images to Documentation folder
    images_dir = os.path.join(item_folder, "images")
    docs_images_dir = os.path.join(docs_dir, "images")
    os.makedirs(docs_images_dir, exist_ok=True)
    
    if os.path.exists(images_dir):
        for img in os.listdir(images_dir):
            src_img = os.path.join(images_dir, img)
            dst_img = os.path.join(docs_images_dir, img)
            if os.path.isfile(src_img):
                shutil.copy2(src_img, dst_img)
    
    # Create README.md
    readme_content = f"# {item.get('title', 'Booth Item')}\n\n"
    readme_content += item.get("description", "No description available.")
    readme_content += f"\n\nSource: {item.get('url', '')}"
    
    with open(os.path.join(package_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    # Create package.json
    manifest = create_package_manifest(item)
    with open(os.path.join(package_dir, "package.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    return package_id, package_dir

def generate_repository_index(repository_path, repo_name="Booth Assets Collection", repo_id="com.boothassetsmanager.repository", repo_author="booth-assets-manager@example.com"):
    """Generate the index.json file for the VCC repository."""
    packages_dir = os.path.join(repository_path, "Packages")
    index_path = os.path.join(repository_path, "index.json")
    
    # Prepare repository data
    repo_data = {
        "name": repo_name,
        "id": repo_id,
        "url": f"file:///{os.path.abspath(index_path).replace(os.sep, '/')}",
        "author": repo_author,
        "packages": {}
    }
    
    # Scan packages directory
    if os.path.exists(packages_dir):
        for package_dir in os.listdir(packages_dir):
            package_path = os.path.join(packages_dir, package_dir)
            if os.path.isdir(package_path):
                manifest_path = os.path.join(package_path, "package.json")
                
                if os.path.exists(manifest_path):
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        try:
                            manifest = json.load(f)
                            package_id = manifest.get("name")
                            version = manifest.get("version", "1.0.0")
                            
                            # Add to packages dictionary
                            if package_id:
                                if package_id not in repo_data["packages"]:
                                    repo_data["packages"][package_id] = {"versions": {}}
                                
                                repo_data["packages"][package_id]["versions"][version] = manifest
                        except json.JSONDecodeError:
                            print(f"Error parsing manifest: {manifest_path}")
    
    # Write index.json
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(repo_data, f, indent=2, ensure_ascii=False)
    
    return index_path

def get_vcc_protocol_url(repository_path):
    """Generate a VCC protocol URL to add the repository."""
    index_path = os.path.join(repository_path, "index.json")
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"Repository index not found at {index_path}")
    
    # Format the file URL properly
    file_url = f"file:///{os.path.abspath(index_path).replace(os.sep, '/')}"
    encoded_url = urllib.parse.quote(file_url, safe=':/')
    
    return f"vcc://vpm/addRepo?url={encoded_url}"

def open_vcc_integration(repository_path):
    """Open the VCC protocol URL in the default browser."""
    try:
        vcc_url = get_vcc_protocol_url(repository_path)
        
        # Open URL in default browser
        if platform.system() == "Windows":
            os.startfile(vcc_url)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", vcc_url], check=True)
        else:  # Linux
            subprocess.run(["xdg-open", vcc_url], check=True)
        
        return True
    except Exception as e:
        print(f"Error opening VCC integration: {e}")
        return False

def package_item(item, repository_path, db):
    """Package a single item."""
    if not item:
        print("Invalid item data.")
        return False
    
    try:
        # Create package structure
        package_id, package_dir = create_package_structure(item, repository_path)
        
        # Update database
        db.update_package_info(item["item_id"], package_id, "1.0.0")
        
        # Regenerate repository index
        generate_repository_index(repository_path)
        
        print(f"Created package for {item['title']} ({item['item_id']}).")
        return True
    except Exception as e:
        print(f"Error packaging item {item['item_id']}: {e}")
        return False

def unpackage_item(item, repository_path, db):
    """Remove a package for an item."""
    if not item:
        print("Invalid item data.")
        return False
    
    if not item.get("package_id"):
        print(f"Item {item['item_id']} is not packaged.")
        return False
    
    try:
        # Remove package directory
        package_path = os.path.join(repository_path, "Packages", item["package_id"])
        if os.path.exists(package_path):
            shutil.rmtree(package_path)
        
        # Update database
        db.update_package_info(item["item_id"], None, None, False)
        
        # Regenerate repository index
        generate_repository_index(repository_path)
        
        print(f"Removed package for {item['title']} ({item['item_id']}).")
        return True
    except Exception as e:
        print(f"Error removing package for item {item['item_id']}: {e}")
        return False

def package_all_items(repository_path, db):
    """Package all items in the database."""
    items = db.get_all_items()
    packaged_count = 0
    
    for item in items:
        if not item.get("is_packaged"):
            if package_item(item, repository_path, db):
                packaged_count += 1
    
    if packaged_count > 0:
        generate_repository_index(repository_path)
        print(f"Packaged {packaged_count} items and updated repository index.")
    else:
        print("No new items were packaged.")
    
    return packaged_count

def validate_repository(repository_path):
    """Validate the repository structure and fix common issues."""
    issues = []
    fixes = []
    
    # Check repository directory
    if not os.path.exists(repository_path):
        issues.append(f"Repository directory does not exist: {repository_path}")
        try:
            os.makedirs(repository_path, exist_ok=True)
            fixes.append(f"Created repository directory: {repository_path}")
        except Exception as e:
            issues.append(f"Failed to create repository directory: {e}")
    
    # Check Packages directory
    packages_dir = os.path.join(repository_path, "Packages")
    if not os.path.exists(packages_dir):
        issues.append(f"Packages directory does not exist: {packages_dir}")
        try:
            os.makedirs(packages_dir, exist_ok=True)
            fixes.append(f"Created Packages directory: {packages_dir}")
        except Exception as e:
            issues.append(f"Failed to create Packages directory: {e}")
    
    # Check index.json
    index_path = os.path.join(repository_path, "index.json")
    if not os.path.exists(index_path):
        issues.append(f"Repository index does not exist: {index_path}")
        try:
            generate_repository_index(repository_path)
            fixes.append(f"Generated repository index: {index_path}")
        except Exception as e:
            issues.append(f"Failed to generate repository index: {e}")
    else:
        # Validate index.json format
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                index_data = json.load(f)
                
                # Check required fields
                required_fields = ["name", "id", "url", "author", "packages"]
                missing_fields = [field for field in required_fields if field not in index_data]
                
                if missing_fields:
                    issues.append(f"Repository index missing required fields: {', '.join(missing_fields)}")
                    try:
                        generate_repository_index(repository_path)
                        fixes.append(f"Regenerated repository index with required fields")
                    except Exception as e:
                        issues.append(f"Failed to regenerate repository index: {e}")
        except json.JSONDecodeError:
            issues.append(f"Repository index is not valid JSON: {index_path}")
            try:
                generate_repository_index(repository_path)
                fixes.append(f"Regenerated repository index with valid JSON")
            except Exception as e:
                issues.append(f"Failed to regenerate repository index: {e}")
        except Exception as e:
            issues.append(f"Error reading repository index: {e}")
    
    return {
        "valid": len(issues) == 0 or len(fixes) == len(issues),
        "issues": issues,
        "fixes": fixes
    }

def test_vcc_integration(repository_path):
    """Test the VCC integration and return status."""
    results = {
        "repository_exists": False,
        "index_valid": False,
        "packages_found": 0,
        "vcc_protocol_works": False,
        "overall_status": "Failed"
    }
    
    # Check repository
    if os.path.exists(repository_path):
        results["repository_exists"] = True
        
        # Check index.json
        index_path = os.path.join(repository_path, "index.json")
        if os.path.exists(index_path):
            try:
                with open(index_path, "r", encoding="utf-8") as f:
                    index_data = json.load(f)
                    if all(field in index_data for field in ["name", "id", "url", "packages"]):
                        results["index_valid"] = True
                        results["packages_found"] = sum(len(pkg.get("versions", {})) 
                                                      for pkg in index_data.get("packages", {}).values())
            except:
                pass
        
        # Test VCC protocol
        try:
            vcc_url = get_vcc_protocol_url(repository_path)
            results["vcc_protocol_works"] = bool(vcc_url and vcc_url.startswith("vcc://"))
        except:
            pass
    
    # Overall status
    if results["repository_exists"] and results["index_valid"]:
        if results["packages_found"] > 0:
            results["overall_status"] = "Ready" if results["vcc_protocol_works"] else "Ready (Manual Addition)"
        else:
            results["overall_status"] = "Empty Repository"
    
    return results
