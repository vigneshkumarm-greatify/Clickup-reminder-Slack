#!/usr/bin/env python3
"""
ClickUp List Management Utility

This script helps you manage your ClickUp lists configuration:
- Discover new sprints automatically
- Enable/disable lists
- View current configuration
- Update list settings
"""

import json
import os
import requests
from datetime import datetime
import argparse
from dotenv import load_dotenv

load_dotenv()

def load_config():
    """Load current configuration"""
    config_file = 'clickup_config.json'
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    return {"lists": []}

def save_config(config):
    """Save configuration to file"""
    config_file = 'clickup_config.json'
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"✅ Configuration saved to {config_file}")

def discover_new_sprints():
    """Discover and add new sprint lists"""
    api_key = os.getenv("CLICKUP_API_KEY")
    team_id = os.getenv("CLICKUP_TEAM_ID")
    
    if not api_key or not team_id:
        print("❌ Missing CLICKUP_API_KEY or CLICKUP_TEAM_ID")
        return
    
    print(f"🔍 Discovering sprints for team: {team_id}")
    
    from clickup_fetcher import discover_sprints, update_config_with_discovered_lists
    
    discovered = discover_sprints(team_id, api_key)
    if discovered:
        update_config_with_discovered_lists(discovered)
        print(f"🎯 Discovered {len(discovered)} new sprint lists")
        for sprint in discovered:
            print(f"  ➕ {sprint['name']}")
    else:
        print("✅ No new sprints found")

def list_current_config():
    """Display current configuration"""
    config = load_config()
    lists = config.get('lists', [])
    
    if not lists:
        print("📋 No lists configured")
        return
    
    print(f"📋 Current Configuration ({len(lists)} lists):")
    print("-" * 80)
    
    for i, list_config in enumerate(lists, 1):
        status = "✅ ENABLED" if list_config.get('enabled', True) else "❌ DISABLED"
        list_type = list_config.get('type', 'general').upper()
        
        print(f"{i:2d}. {list_config['name']}")
        print(f"    ID: {list_config['id']}")
        print(f"    Type: {list_type}")
        print(f"    Status: {status}")
        if 'description' in list_config:
            print(f"    Description: {list_config['description']}")
        if list_config.get('discovered'):
            print(f"    Auto-discovered: {list_config.get('discovery_date', 'Unknown')}")
        print()

def enable_disable_list():
    """Enable or disable a specific list"""
    list_current_config()
    
    config = load_config()
    lists = config.get('lists', [])
    
    if not lists:
        return
    
    try:
        choice = int(input("\nSelect list number to toggle: ")) - 1
        if 0 <= choice < len(lists):
            current_status = lists[choice].get('enabled', True)
            lists[choice]['enabled'] = not current_status
            
            action = "disabled" if current_status else "enabled"
            print(f"✅ List '{lists[choice]['name']}' has been {action}")
            
            save_config(config)
        else:
            print("❌ Invalid list number")
    except ValueError:
        print("❌ Please enter a valid number")

def add_manual_list():
    """Manually add a new list"""
    print("➕ Add New List")
    print("-" * 20)
    
    list_id = input("List ID: ").strip()
    if not list_id:
        print("❌ List ID is required")
        return
    
    name = input("List Name: ").strip()
    if not name:
        name = f"List {list_id}"
    
    print("\nList Types:")
    print("1. sprint - Sprint/iteration tasks")
    print("2. feature - Feature development")
    print("3. bug - Bug tracking")
    print("4. general - General tasks")
    
    type_choice = input("Select type (1-4): ").strip()
    type_map = {"1": "sprint", "2": "feature", "3": "bug", "4": "general"}
    list_type = type_map.get(type_choice, "general")
    
    description = input("Description (optional): ").strip()
    
    # Load and update config
    config = load_config()
    new_list = {
        "id": list_id,
        "name": name,
        "type": list_type,
        "enabled": True,
        "manually_added": True,
        "added_date": datetime.now().isoformat()
    }
    
    if description:
        new_list["description"] = description
    
    config["lists"].append(new_list)
    save_config(config)
    
    print(f"✅ Added new {list_type} list: {name}")

def main():
    parser = argparse.ArgumentParser(description="ClickUp List Management Utility")
    parser.add_argument('--discover', '-d', action='store_true', 
                       help='Discover new sprint lists')
    parser.add_argument('--list', '-l', action='store_true', 
                       help='List current configuration')
    parser.add_argument('--toggle', '-t', action='store_true', 
                       help='Enable/disable a list')
    parser.add_argument('--add', '-a', action='store_true', 
                       help='Manually add a new list')
    
    args = parser.parse_args()
    
    print("🎯 ClickUp List Manager")
    print("=" * 50)
    
    if args.discover:
        discover_new_sprints()
    elif args.list:
        list_current_config()
    elif args.toggle:
        enable_disable_list()
    elif args.add:
        add_manual_list()
    else:
        # Interactive mode
        while True:
            print("\nWhat would you like to do?")
            print("1. 🔍 Discover new sprint lists")
            print("2. 📋 List current configuration")
            print("3. ⚡ Enable/disable a list")
            print("4. ➕ Add a new list manually")
            print("5. 🚪 Exit")
            
            choice = input("\nSelect option (1-5): ").strip()
            
            if choice == "1":
                discover_new_sprints()
            elif choice == "2":
                list_current_config()
            elif choice == "3":
                enable_disable_list()
            elif choice == "4":
                add_manual_list()
            elif choice == "5":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1-5.")

if __name__ == "__main__":
    main() 