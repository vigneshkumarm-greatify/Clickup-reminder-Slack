#!/usr/bin/env python3
"""
User Mapping Management Utility

This script helps you manage ClickUp to Slack username mappings:
- Add new user mappings
- View current mappings
- Update existing mappings
- Test mappings
"""

import json
import os
import argparse
from dotenv import load_dotenv

load_dotenv()

def load_mappings():
    """Load current user mappings"""
    mapping_file = os.getenv('USER_MAPPING_FILE', 'user_mapping.json')
    if os.path.exists(mapping_file):
        with open(mapping_file, 'r') as f:
            return json.load(f), mapping_file
    
    # Default configuration
    default_config = {
        "user_mappings": {},
        "default_mention": "@channel",
        "fallback_behavior": "use_clickup_name"
    }
    return default_config, mapping_file

def save_mappings(config, mapping_file):
    """Save user mappings to file"""
    with open(mapping_file, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"✅ Mappings saved to {mapping_file}")

def show_mappings():
    """Display current user mappings"""
    config, mapping_file = load_mappings()
    mappings = config.get("user_mappings", {})
    
    if not mappings:
        print("📋 No user mappings configured")
        return
    
    print(f"📋 Current User Mappings ({len(mappings)} users):")
    print("-" * 70)
    print(f"{'ClickUp Username':<25} → {'Slack User ID':<35}")
    print("-" * 70)
    
    for clickup_user, slack_user_id in mappings.items():
        # Format display based on whether it's a Slack user ID or display name
        if slack_user_id.startswith('U'):
            display_format = f"<@{slack_user_id}>"
        else:
            display_format = f"@{slack_user_id}"
        print(f"{clickup_user:<25} → {display_format:<34}")
    
    print("-" * 70)
    print(f"📁 Config file: {mapping_file}")
    print(f"🔄 Fallback behavior: {config.get('fallback_behavior', 'use_clickup_name')}")
    print(f"📢 Default mention: {config.get('default_mention', '@channel')}")

def add_mapping():
    """Add a new user mapping"""
    config, mapping_file = load_mappings()
    
    print("➕ Add New User Mapping")
    print("-" * 30)
    
    clickup_user = input("ClickUp username: ").strip()
    if not clickup_user:
        print("❌ ClickUp username is required")
        return
    
    slack_user = input("Slack username (without @): ").strip()
    if not slack_user:
        print("❌ Slack username is required")
        return
    
    # Add to mappings
    config["user_mappings"][clickup_user] = slack_user
    save_mappings(config, mapping_file)
    
    print(f"✅ Added mapping: {clickup_user} → @{slack_user}")

def test_mapping():
    """Test a user mapping"""
    config, _ = load_mappings()
    
    print("🧪 Test User Mapping")
    print("-" * 25)
    
    clickup_user = input("Enter ClickUp username to test: ").strip()
    if not clickup_user:
        print("❌ Username is required")
        return
    
    # Import the function to test
    import sys
    sys.path.append('.')
    from gpt_generator import get_slack_username
    
    slack_mention = get_slack_username(clickup_user)
    print(f"📤 ClickUp: '{clickup_user}' → Slack: '{slack_mention}'")

def update_settings():
    """Update fallback settings"""
    config, mapping_file = load_mappings()
    
    print("⚙️  Update Settings")
    print("-" * 20)
    
    print("Current settings:")
    print(f"  Fallback behavior: {config.get('fallback_behavior')}")
    print(f"  Default mention: {config.get('default_mention')}")
    print()
    
    print("Fallback behavior options:")
    print("1. use_clickup_name - Use @clickup_username if no mapping")
    print("2. use_default - Use default mention if no mapping")
    
    choice = input("Select fallback behavior (1-2): ").strip()
    if choice == "1":
        config["fallback_behavior"] = "use_clickup_name"
    elif choice == "2":
        config["fallback_behavior"] = "use_default"
        default = input("Enter default mention (e.g., @channel, @here): ").strip()
        if default:
            config["default_mention"] = default
    
    save_mappings(config, mapping_file)

def bulk_import():
    """Import multiple mappings from input"""
    config, mapping_file = load_mappings()
    
    print("📥 Bulk Import Mappings")
    print("-" * 30)
    print("Enter mappings in format: clickup_user=slack_user")
    print("One mapping per line. Empty line to finish.")
    print("Example: john.smith=jsmith")
    print()
    
    added_count = 0
    while True:
        line = input("Mapping: ").strip()
        if not line:
            break
        
        try:
            clickup_user, slack_user = line.split('=', 1)
            clickup_user = clickup_user.strip()
            slack_user = slack_user.strip()
            
            if clickup_user and slack_user:
                config["user_mappings"][clickup_user] = slack_user
                added_count += 1
                print(f"  ✅ Added: {clickup_user} → @{slack_user}")
            else:
                print(f"  ❌ Invalid format: {line}")
        except ValueError:
            print(f"  ❌ Invalid format: {line}")
    
    if added_count > 0:
        save_mappings(config, mapping_file)
        print(f"✅ Added {added_count} mappings")

def main():
    parser = argparse.ArgumentParser(description="User Mapping Management Utility")
    parser.add_argument('--show', '-s', action='store_true', 
                       help='Show current mappings')
    parser.add_argument('--add', '-a', action='store_true', 
                       help='Add a new mapping')
    parser.add_argument('--test', '-t', action='store_true', 
                       help='Test a mapping')
    parser.add_argument('--settings', action='store_true', 
                       help='Update settings')
    parser.add_argument('--import', '-i', action='store_true', 
                       help='Bulk import mappings')
    
    args = parser.parse_args()
    
    print("👤 User Mapping Manager")
    print("=" * 40)
    
    if args.show:
        show_mappings()
    elif args.add:
        add_mapping()
    elif args.test:
        test_mapping()
    elif args.settings:
        update_settings()
    elif getattr(args, 'import'):
        bulk_import()
    else:
        # Interactive mode
        while True:
            print("\nWhat would you like to do?")
            print("1. 📋 Show current mappings")
            print("2. ➕ Add new mapping")
            print("3. 🧪 Test a mapping")
            print("4. ⚙️  Update settings")
            print("5. 📥 Bulk import mappings")
            print("6. 🚪 Exit")
            
            choice = input("\nSelect option (1-6): ").strip()
            
            if choice == "1":
                show_mappings()
            elif choice == "2":
                add_mapping()
            elif choice == "3":
                test_mapping()
            elif choice == "4":
                update_settings()
            elif choice == "5":
                bulk_import()
            elif choice == "6":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1-6.")

if __name__ == "__main__":
    main() 