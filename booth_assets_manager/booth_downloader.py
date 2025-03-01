import os
import re
import json
import asyncio
import urllib.parse
from datetime import datetime
from tqdm import tqdm
from playwright.async_api import async_playwright
from .settings import settings

class BoothDownloader:
    """
    Handles downloading files from Booth using browser automation.
    """
    def __init__(self):
        self.cookies_path = settings.get("auth_cookies_file")
        self.download_base_dir = settings.get("download_directory", "BoothDownloads")
        os.makedirs(self.download_base_dir, exist_ok=True)
    
    def sanitize_filename(self, filename):
        """Sanitize a string to be used as a safe filename."""
        return re.sub(r'[\\/*?:"<>|]', "", filename.replace(" ", "_"))
    
    async def get_purchased_items(self):
        """
        Fetch list of purchased items from Booth.
        Returns a list of dictionaries with item details.
        """
        if not self.cookies_path or not os.path.exists(self.cookies_path):
            raise Exception("Not authenticated. Please login first.")
        
        purchases = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            
            # Load cookies
            with open(self.cookies_path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            await context.add_cookies(cookies)
            page = await context.new_page()
            
            # Go to orders page
            await page.goto('https://booth.pm/orders')
            
            # Check if we're redirected to login
            if '/users/sign_in' in page.url:
                await browser.close()
                raise Exception("Session expired. Please login again.")
            
            # Wait for orders to load
            await page.wait_for_selector('.orders-item', timeout=10000)
            
            # Extract order items
            order_items = await page.query_selector_all('.orders-item')
            
            for item in order_items:
                # Extract title and URL
                title_el = await item.query_selector('.orders-item-title')
                if title_el:
                    link_el = await title_el.query_selector('a')
                    if link_el:
                        title = await link_el.text_content()
                        url = await link_el.get_attribute('href')
                        url = urllib.parse.urljoin('https://booth.pm', url)
                        
                        # Extract item ID from URL
                        match = re.search(r'/(?:en/)?items/(\d+)', url)
                        item_id = match.group(1) if match else None
                        
                        if item_id:
                            # Extract additional details like purchase date, price
                            date_el = await item.query_selector('.orders-item-date')
                            purchase_date = await date_el.text_content() if date_el else None
                            
                            price_el = await item.query_selector('.orders-item-price')
                            price_text = await price_el.text_content() if price_el else None
                            
                            purchases.append({
                                'item_id': item_id,
                                'title': title.strip(),
                                'url': url,
                                'purchase_date': purchase_date.strip() if purchase_date else None,
                                'price': price_text.strip() if price_text else None
                            })
            
            await browser.close()
        
        return purchases
    
    async def get_download_links(self, item_id):
        """
        Get download links for a purchased item.
        Returns a list of dictionaries with file details.
        """
        if not self.cookies_path or not os.path.exists(self.cookies_path):
            raise Exception("Not authenticated. Please login first.")
        
        download_links = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            
            # Load cookies
            with open(self.cookies_path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            await context.add_cookies(cookies)
            page = await context.new_page()
            
            # Go to item's download page
            await page.goto(f'https://booth.pm/items/{item_id}/downloads')
            
            # Check if we're redirected to login
            if '/users/sign_in' in page.url:
                await browser.close()
                raise Exception("Session expired. Please login again.")
            
            # Check if we have access to download this item
            error_el = await page.query_selector('.l-alerts')
            if error_el:
                error_text = await error_el.text_content()
                if "not purchased" in error_text.lower():
                    await browser.close()
                    raise Exception(f"You have not purchased item {item_id}")
            
            # Wait for download links to load
            await page.wait_for_selector('.download-link, .l-alerts', timeout=10000)
            
            # Extract download links
            download_elements = await page.query_selector_all('.download-item')
            
            for element in download_elements:
                # Get filename
                name_el = await element.query_selector('.file-name')
                if not name_el:
                    continue
                
                filename = await name_el.text_content()
                filename = filename.strip()
                
                # Get file size
                size_el = await element.query_selector('.file-size')
                file_size = await size_el.text_content() if size_el else None
                
                # Get download link
                link_el = await element.query_selector('.download-link')
                if not link_el:
                    continue
                
                href = await link_el.get_attribute('href')
                if not href:
                    continue
                
                download_url = urllib.parse.urljoin('https://booth.pm', href)
                
                download_links.append({
                    'filename': filename,
                    'size': file_size.strip() if file_size else None,
                    'url': download_url
                })
            
            await browser.close()
        
        return download_links
    
    async def download_file(self, download_url, item_id, item_title, filename):
        """
        Download a file using browser automation.
        Returns the path to the downloaded file.
        """
        if not self.cookies_path or not os.path.exists(self.cookies_path):
            raise Exception("Not authenticated. Please login first.")
        
        # Create folder for the item
        safe_title = self.sanitize_filename(item_title)
        item_folder = os.path.join(self.download_base_dir, f"{item_id}_{safe_title}")
        downloads_folder = os.path.join(item_folder, "downloads")
        os.makedirs(downloads_folder, exist_ok=True)
        
        # Generate file path
        file_path = os.path.join(downloads_folder, filename)
        
        # Skip if file already exists and is not empty
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            print(f"File already exists: {file_path}")
            return file_path
        
        print(f"Downloading {filename} to {file_path}...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            # Set download path
            context = await browser.new_context(
                accept_downloads=True,
                # Firefox settings for preventing file chooser dialog
                java_script_enabled=True,
                viewport={'width': 1280, 'height': 720}
            )
            
            # Set download behavior to save all downloads
            await context.set_default_timeout(120000)  # 2 minutes timeout
            
            # Load cookies
            with open(self.cookies_path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            await context.add_cookies(cookies)
            page = await context.new_page()
            
            # Create download listener
            download_promise = page.wait_for_download()
            
            # Visit download URL
            try:
                await page.goto(download_url, wait_until='domcontentloaded')
            except Exception as e:
                print(f"Error navigating to download URL: {e}")
                await browser.close()
                return None
            
            # Check if redirected to login
            if '/users/sign_in' in page.url:
                await browser.close()
                raise Exception("Session expired. Please login again.")
            
            # Wait for download to start
            try:
                download = await download_promise
                
                # Initialize progress bar
                progress_bar = tqdm(total=100, desc=f"Downloading {filename}", unit="%")
                
                # Save the download to the specified path
                await download.save_as(file_path)
                
                # Update progress bar to 100%
                progress_bar.update(100 - progress_bar.n)
                progress_bar.close()
                
                print(f"Download complete: {file_path}")
                await browser.close()
                return file_path
                
            except Exception as e:
                print(f"Error downloading file: {e}")
                await browser.close()
                return None

# Helper functions to run async methods
def get_purchased_items():
    """Get list of purchased items."""
    downloader = BoothDownloader()
    return asyncio.run(downloader.get_purchased_items())

def get_download_links(item_id):
    """Get download links for an item."""
    downloader = BoothDownloader()
    return asyncio.run(downloader.get_download_links(item_id))

def download_file(download_url, item_id, item_title, filename):
    """Download a file."""
    downloader = BoothDownloader()
    return asyncio.run(downloader.download_file(download_url, item_id, item_title, filename))

# Advanced functionality for parallel downloads
async def download_multiple_files(item_id, item_title, download_links, max_concurrent=3):
    """Download multiple files concurrently with limited concurrency."""
    downloader = BoothDownloader()
    semaphore = asyncio.Semaphore(max_concurrent)
    results = []
    
    async def download_with_limit(link):
        async with semaphore:  # Limit concurrent downloads
            result = await downloader.download_file(
                link['url'], 
                item_id, 
                item_title, 
                link['filename']
            )
            return {
                'filename': link['filename'],
                'path': result,
                'success': result is not None
            }
    
    # Create download tasks
    tasks = [download_with_limit(link) for link in download_links]
    
    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks)
    
    return results

def download_all_files(item_id, item_title, max_concurrent=3):
    """Download all files for an item with concurrency control."""
    try:
        # Get download links
        links = get_download_links(item_id)
        
        if not links:
            print(f"No download links found for item {item_id}")
            return []
        
        # Download all files concurrently
        results = asyncio.run(download_multiple_files(
            item_id, 
            item_title, 
            links, 
            max_concurrent
        ))
        
        # Print summary
        successful = [r for r in results if r['success']]
        print(f"\nDownload summary for {item_title}:")
        print(f"  Total files: {len(results)}")
        print(f"  Successfully downloaded: {len(successful)}")
        print(f"  Failed: {len(results) - len(successful)}")
        
        return results
        
    except Exception as e:
        print(f"Error downloading files for item {item_id}: {e}")
        return []
