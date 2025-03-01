#!/usr/bin/env python3
import argparse
import os
import sys
from .database import Database
from .settings import settings
from .vcc_integration import (
    package_item,
    unpackage_item,
    package_all_items,
    generate_repository_index,
    open_vcc_integration,
    validate_repository,
    test_vcc_integration
)

def vcc_cli():
    """Command-line interface for VCC repository management."""
    parser = argparse.ArgumentParser(
        description="Manage VCC repository for Booth Assets Manager"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Enable command
    enable_parser = subparsers.add_parser("enable", help="Enable VCC integration")
    
    # Disable command
    disable_parser = subparsers.add_parser("disable", help="Disable VCC integration")
    
    # Package command
    package_parser = subparsers.add_parser("package", help="Package an item")
    package_parser.add_argument("item_id", help="ID of the item to package")
    
    # Unpackage command
    unpackage_parser = subparsers.add_parser("unpackage", help="Remove a package")
    unpackage_parser.add_argument("item_id", help="ID of the item to unpackage")
    
    # Package all command
    package_all_parser = subparsers.add_parser("package-all", help="Package all items")
    
    # Regenerate command
    regenerate_parser = subparsers.add_parser("regenerate", help="Regenerate repository index")
    
    # Add to VCC command
    add_to_vcc_parser = subparsers.add_parser("add-to-vcc", help="Add repository to VCC")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate repository structure")
    validate_parser.add_argument("--fix", action="store_true", help="Fix issues automatically")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show repository status")
    
    # Settings command
    settings_parser = subparsers.add_parser("settings", help="Show or update settings")
    settings_parser.add_argument("--repository-path", help="Set repository path")
    settings_parser.add_argument("--repository-name", help="Set repository name")
    settings_parser.add_argument("--repository-id", help="Set repository ID")
    settings_parser.add_argument("--repository-author", help="Set repository author")
    settings_parser.add_argument("--auto-package", action="store_true", help="Enable auto-packaging of new items")
    settings_parser.add_argument("--no-auto-package", action="store_true", help="Disable auto-packaging of new items")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Initialize database
    db = Database()
    
    # Execute command
    if args.command == "enable":
        settings.set_vcc_enabled(True)
        settings.ensure_repository_structure()
        print("VCC integration enabled.")
        
        # Generate initial repository index if it doesn't exist
        repo_path = settings.get_repository_path()
        index_path = os.path.join(repo_path, "index.json")
        if not os.path.exists(index_path):
            generate_repository_index(
                repo_path,
                settings.get_repository_name(),
                settings.get_repository_id(),
                settings.get_repository_author()
            )
            print(f"Repository index created at {index_path}")
    
    elif args.command == "disable":
        settings.set_vcc_enabled(False)
        print("VCC integration disabled.")
    
    elif args.command == "package":
        if not settings.is_vcc_enabled():
            print("VCC integration is not enabled. Use 'vcc enable' first.")
            return 1
        
        item = db.get_item(args.item_id)
        if not item:
            print(f"Item {args.item_id} not found in database.")
            return 1
        
        if package_item(item, settings.get_repository_path(), db):
            print(f"Item {args.item_id} packaged successfully.")
        else:
            print(f"Failed to package item {args.item_id}.")
            return 1
    
    elif args.command == "unpackage":
        if not settings.is_vcc_enabled():
            print("VCC integration is not enabled. Use 'vcc enable' first.")
            return 1
        
        item = db.get_item(args.item_id)
        if not item:
            print(f"Item {args.item_id} not found in database.")
            return 1
        
        if unpackage_item(item, settings.get_repository_path(), db):
            print(f"Item {args.item_id} unpackaged successfully.")
        else:
            print(f"Failed to unpackage item {args.item_id}.")
            return 1
    
    elif args.command == "package-all":
        if not settings.is_vcc_enabled():
            print("VCC integration is not enabled. Use 'vcc enable' first.")
            return 1
        
        count = package_all_items(settings.get_repository_path(), db)
        print(f"Packaged {count} items.")
    
    elif args.command == "regenerate":
        if not settings.is_vcc_enabled():
            print("VCC integration is not enabled. Use 'vcc enable' first.")
            return 1
        
        index_path = generate_repository_index(
            settings.get_repository_path(),
            settings.get_repository_name(),
            settings.get_repository_id(),
            settings.get_repository_author()
        )
        print(f"Repository index regenerated at {index_path}")
    
    elif args.command == "add-to-vcc":
        if not settings.is_vcc_enabled():
            print("VCC integration is not enabled. Use 'vcc enable' first.")
            return 1
        
        if open_vcc_integration(settings.get_repository_path()):
            print("VCC integration link opened in browser.")
        else:
            print("Failed to open VCC integration link. Please add the repository manually.")
            print(f"Repository path: file:///{os.path.abspath(os.path.join(settings.get_repository_path(), 'index.json')).replace(os.sep, '/')}")
            return 1
    
    elif args.command == "validate":
        if not settings.is_vcc_enabled():
            print("VCC integration is not enabled. Use 'vcc enable' first.")
            return 1
        
        result = validate_repository(settings.get_repository_path())
        
        if result["valid"]:
            print("Repository structure is valid.")
        else:
            print("Repository structure has issues:")
            for issue in result["issues"]:
                print(f"- {issue}")
            
            if result["fixes"] and args.fix:
                print("\nFixed issues:")
                for fix in result["fixes"]:
                    print(f"- {fix}")
            elif result["fixes"]:
                print("\nUse --fix to automatically fix these issues.")
    
    elif args.command == "status":
        if not settings.is_vcc_enabled():
            print("VCC integration is not enabled. Use 'vcc enable' first.")
            return 1
        
        # Get repository status
        repo_path = settings.get_repository_path()
        status = test_vcc_integration(repo_path)
        
        print(f"Repository Path: {repo_path}")
        print(f"Repository Exists: {'Yes' if status['repository_exists'] else 'No'}")
        print(f"Index Valid: {'Yes' if status['index_valid'] else 'No'}")
        print(f"Packages Found: {status['packages_found']}")
        print(f"VCC Protocol Works: {'Yes' if status['vcc_protocol_works'] else 'No'}")
        print(f"Overall Status: {status['overall_status']}")
        
        # Get packaged items count
        packaged_items = db.get_packaged_items()
        print(f"Packaged Items: {len(packaged_items)}")
        
        # Show repository settings
        print("\nRepository Settings:")
        print(f"Name: {settings.get_repository_name()}")
        print(f"ID: {settings.get_repository_id()}")
        print(f"Author: {settings.get_repository_author()}")
        print(f"Auto-Package New Items: {'Yes' if settings.get_auto_package_new_items() else 'No'}")
    
    elif args.command == "settings":
        # Update settings if provided
        if args.repository_path:
            settings.config["repository_path"] = args.repository_path
            print(f"Repository path set to: {args.repository_path}")
        
        if args.repository_name:
            settings.set_repository_name(args.repository_name)
            print(f"Repository name set to: {args.repository_name}")
        
        if args.repository_id:
            settings.set_repository_id(args.repository_id)
            print(f"Repository ID set to: {args.repository_id}")
        
        if args.repository_author:
            settings.set_repository_author(args.repository_author)
            print(f"Repository author set to: {args.repository_author}")
        
        if args.auto_package:
            settings.set_auto_package_new_items(True)
            print("Auto-packaging of new items enabled.")
        
        if args.no_auto_package:
            settings.set_auto_package_new_items(False)
            print("Auto-packaging of new items disabled.")
        
        # Save settings if any changes were made
        if any([args.repository_path, args.repository_name, args.repository_id, 
                args.repository_author, args.auto_package, args.no_auto_package]):
            settings.save()
        
        # Show current settings
        print("\nCurrent Settings:")
        print(f"VCC Integration Enabled: {'Yes' if settings.is_vcc_enabled() else 'No'}")
        print(f"Repository Path: {settings.get_repository_path()}")
        print(f"Repository Name: {settings.get_repository_name()}")
        print(f"Repository ID: {settings.get_repository_id()}")
        print(f"Repository Author: {settings.get_repository_author()}")
        print(f"Auto-Package New Items: {'Yes' if settings.get_auto_package_new_items() else 'No'}")
    
    else:
        parser.print_help()
    
    return 0

def main():
    """Entry point for the VCC CLI."""
    sys.exit(vcc_cli())

if __name__ == "__main__":
    main()
