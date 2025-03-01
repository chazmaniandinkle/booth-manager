#!/usr/bin/env python3
import argparse
import os
import sys
import time
import json
import asyncio
from datetime import datetime
from tqdm import tqdm
from .browser_auth import BrowserAuth, interactive_login, check_auth_status
from .booth_downloader import (
    BoothDownloader, 
    get_purchased_items, 
    get_download_links, 
    download_file,
    download_all_files
)
from .database import Database
from .settings import settings

def auth_cli():
    """Command-line interface for Booth authentication and downloads."""
    parser = argparse.ArgumentParser(
        description="Manage Booth authentication and downloads"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Login command - now simpler, no arguments needed
    login_parser = subparsers.add_parser("login", help="Open browser for interactive Booth login")
    
    # Logout command
    logout_parser = subparsers.add_parser("logout", help="Logout and clear session data")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Check authentication status")
    
    # Purchases command
    purchases_parser = subparsers.add_parser("purchases", help="List purchased items")
    purchases_parser.add_argument("--update-db", action="store_true", help="Update database with purchased items")
    
    # Download command
    download_parser = subparsers.add_parser("download", help="Download files for purchased items")
    download_parser.add_argument("--item-id", help="ID of the item to download")
    download_parser.add_argument("--all", action="store_true", help="Download all purchased items")
    download_parser.add_argument("--output-dir", help="Base directory to save downloaded files")
    download_parser.add_argument("--concurrent", type=int, default=3, help="Maximum concurrent downloads (default: 3)")
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command == "login":
        print("Launching browser for Booth login...")
        if interactive_login():
            print("Authentication successful!")
        else:
            print("Authentication failed or was cancelled.")
            return 1
    
    elif args.command == "logout":
        cookies_file = settings.get("auth_cookies_file")
        if cookies_file and os.path.exists(cookies_file):
            try:
                os.remove(cookies_file)
                print("Logged out successfully.")
            except Exception as e:
                print(f"Error removing cookies file: {e}")
                return 1
        else:
            print("No active session found.")
        
        # Clear auth settings
        settings.set("auth_cookies_file", None)
        settings.set("last_login", None)
        settings.save()
    
    elif args.command == "status":
        print("Checking authentication status...")
        if check_auth_status():
            print("✅ You are authenticated with Booth.")
            last_login = settings.get("last_login")
            if last_login:
                try:
                    login_date = datetime.fromisoformat(last_login)
                    print(f"Last login: {login_date.strftime('%Y-%m-%d %H:%M:%S')}")
                except:
                    pass
        else:
            print("❌ Not authenticated or session expired. Please log in again.")
            return 1
    
    elif args.command == "purchases":
        print("Checking authentication status...")
        if not check_auth_status():
            print("Not authenticated. Please run 'booth-auth login' first.")
            return 1
        
        print("Fetching purchases...")
        try:
            purchases = get_purchased_items()
            
            if not purchases:
                print("No purchases found.")
                return 0
            
            print(f"\nFound {len(purchases)} purchased items:")
            for i, item in enumerate(purchases, 1):
                print(f"{i}. {item['title']} (ID: {item['item_id']})")
                print(f"   URL: {item['url']}")
                if item.get('purchase_date'):
                    print(f"   Purchased: {item['purchase_date']}")
                if item.get('price'):
                    print(f"   Price: {item['price']}")
                print()
            
            # Update database if requested
            if args.update_db:
                print("\nUpdating database with purchased items...")
                db = Database()
                
                for item in purchases:
                    # Check if item exists in database
                    existing_item = db.get_item(item['item_id'])
                    
                    if existing_item:
                        # Update existing item
                        db.update_item(
                            item['item_id'],
                            is_purchased=True,
                            purchase_date=item.get('purchase_date'),
                            purchase_price=item.get('price')
                        )
                        print(f"Updated item in database: {item['title']}")
                    else:
                        # Add new item
                        db.add_item(
                            item_id=item['item_id'],
                            title=item['title'],
                            url=item['url'],
                            is_purchased=True,
                            purchase_date=item.get('purchase_date'),
                            purchase_price=item.get('price')
                        )
                        print(f"Added new item to database: {item['title']}")
                
                print("Database update complete.")
            
        except Exception as e:
            print(f"Error fetching purchases: {e}")
            return 1
    
    elif args.command == "download":
        print("Checking authentication status...")
        if not check_auth_status():
            print("Not authenticated. Please run 'booth-auth login' first.")
            return 1
        
        # Set output directory if specified
        if args.output_dir:
            settings.set("download_directory", args.output_dir)
            settings.save()
            print(f"Download directory set to: {args.output_dir}")
        
        # Download specific item
        if args.item_id:
            try:
                # Get item details
                purchases = get_purchased_items()
                item = next((p for p in purchases if p['item_id'] == args.item_id), None)
                
                if not item:
                    print(f"Item ID {args.item_id} not found in your purchases.")
                    return 1
                
                print(f"Downloading files for: {item['title']} (ID: {item['item_id']})")
                
                # Download all files for the item
                results = download_all_files(
                    item['item_id'], 
                    item['title'],
                    max_concurrent=args.concurrent
                )
                
                if not results:
                    print("No files were downloaded.")
                    return 1
                
                # Update database
                db = Database()
                for result in results:
                    if result['success'] and result['path']:
                        # Add download to database
                        db.add_or_update_download(
                            item_id=item['item_id'],
                            filename=result['filename'],
                            local_path=result['path'],
                            download_date=datetime.now().isoformat()
                        )
                
                print("Download complete and database updated.")
                
            except Exception as e:
                print(f"Error downloading item: {e}")
                return 1
        
        # Download all items
        elif args.all:
            try:
                # Get all purchases
                purchases = get_purchased_items()
                
                if not purchases:
                    print("No purchases found.")
                    return 0
                
                print(f"Downloading files for {len(purchases)} items...")
                
                # Download each item
                for i, item in enumerate(purchases, 1):
                    print(f"\n[{i}/{len(purchases)}] Processing: {item['title']} (ID: {item['item_id']})")
                    
                    # Download all files for the item
                    results = download_all_files(
                        item['item_id'], 
                        item['title'],
                        max_concurrent=args.concurrent
                    )
                    
                    # Update database
                    if results:
                        db = Database()
                        for result in results:
                            if result['success'] and result['path']:
                                # Add download to database
                                db.add_or_update_download(
                                    item_id=item['item_id'],
                                    filename=result['filename'],
                                    local_path=result['path'],
                                    download_date=datetime.now().isoformat()
                                )
                
                print("\nAll downloads complete.")
                
            except Exception as e:
                print(f"Error downloading items: {e}")
                return 1
        
        else:
            print("Please specify --item-id or --all to download files.")
            return 1
    
    else:
        parser.print_help()
    
    return 0

def main():
    """Entry point for the Auth CLI."""
    sys.exit(auth_cli())

if __name__ == "__main__":
    main()
