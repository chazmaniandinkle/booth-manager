#!/usr/bin/env python3
"""
Test script for VCC integration.
This script tests the VCC integration functionality by:
1. Enabling VCC integration
2. Creating the repository structure
3. Packaging a test item
4. Generating the repository index
5. Testing the VCC protocol URL
"""

import os
import sys
import argparse
from booth_assets_manager.database import Database
from booth_assets_manager.settings import settings
from booth_assets_manager.vcc_integration import (
    package_item,
    generate_repository_index,
    validate_repository,
    test_vcc_integration,
    get_vcc_protocol_url
)

def main():
    parser = argparse.ArgumentParser(description="Test VCC integration")
    parser.add_argument("--item-id", help="Item ID to package (if not provided, will use the first item in the database)")
    args = parser.parse_args()
    
    print("Testing VCC integration...")
    
    # Step 1: Enable VCC integration
    settings.set_vcc_enabled(True)
    print(f"VCC integration enabled: {settings.is_vcc_enabled()}")
    
    # Step 2: Create repository structure
    repo_path = settings.get_repository_path()
    settings.ensure_repository_structure()
    print(f"Repository structure created at: {repo_path}")
    
    # Step 3: Package a test item
    db = Database()
    
    if args.item_id:
        item = db.get_item(args.item_id)
        if not item:
            print(f"Item {args.item_id} not found in database.")
            return 1
    else:
        # Get the first item from the database
        items = db.get_all_items()
        if not items:
            print("No items found in database. Please add some items first.")
            return 1
        item = items[0]
    
    print(f"Packaging item: {item['title']} ({item['item_id']})")
    if package_item(item, repo_path, db):
        print(f"Item {item['item_id']} packaged successfully.")
    else:
        print(f"Failed to package item {item['item_id']}.")
        return 1
    
    # Step 4: Generate repository index
    index_path = generate_repository_index(
        repo_path,
        settings.get_repository_name(),
        settings.get_repository_id(),
        settings.get_repository_author()
    )
    print(f"Repository index generated at: {index_path}")
    
    # Step 5: Validate repository
    validation = validate_repository(repo_path)
    if validation["valid"]:
        print("Repository validation: PASSED")
    else:
        print("Repository validation: FAILED")
        print("Issues:")
        for issue in validation["issues"]:
            print(f"- {issue}")
        return 1
    
    # Step 6: Test VCC integration
    status = test_vcc_integration(repo_path)
    print("\nVCC Integration Status:")
    print(f"Repository Exists: {'Yes' if status['repository_exists'] else 'No'}")
    print(f"Index Valid: {'Yes' if status['index_valid'] else 'No'}")
    print(f"Packages Found: {status['packages_found']}")
    print(f"VCC Protocol Works: {'Yes' if status['vcc_protocol_works'] else 'No'}")
    print(f"Overall Status: {status['overall_status']}")
    
    # Step 7: Get VCC protocol URL
    try:
        vcc_url = get_vcc_protocol_url(repo_path)
        print(f"\nVCC Protocol URL: {vcc_url}")
        print("To add this repository to VCC, run: booth-vcc add-to-vcc")
    except Exception as e:
        print(f"Failed to generate VCC protocol URL: {e}")
        return 1
    
    print("\nVCC integration test completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
