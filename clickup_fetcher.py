import requests
import os
import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

def get_list_config():
    """Get list configuration from environment or config file"""
    # Try to load from config file first
    config_file = os.getenv('CLICKUP_CONFIG_FILE', 'clickup_config.json')
    if os.path.exists(config_file):
        logger.info(f"📁 Loading ClickUp configuration from {config_file}")
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                return config.get('lists', [])
        except Exception as e:
            logger.warning(f"⚠️  Failed to load config file: {e}")
    
    # Fallback to environment variable (backward compatibility)
    list_id = os.getenv("CLICKUP_LIST_ID")
    if list_id:
        logger.info("📋 Using single list from environment variable")
        return [{
            "id": list_id,
            "name": "Default List",
            "type": "general",
            "enabled": True
        }]
    
    raise ValueError("No ClickUp lists configured. Please set CLICKUP_LIST_ID or create clickup_config.json")

def discover_sprints(team_id: str, api_key: str) -> List[Dict]:
    """Automatically discover sprint lists in a team/space"""
    logger.info(f"🔍 Discovering sprint lists for team: {team_id}")
    
    headers = {"Authorization": api_key}
    
    # Load filtering configuration
    config_file = os.getenv('CLICKUP_CONFIG_FILE', 'clickup_config.json')
    filter_settings = {}
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                filter_settings = config.get('discovery_settings', {})
        except Exception as e:
            logger.warning(f"⚠️  Failed to load filter settings: {e}")
    
    # Default filters
    include_folders = filter_settings.get('include_folders', ['sprint', 'iteration', 'pi', 'release'])
    exclude_folders = filter_settings.get('exclude_folders', ['managex', 'template', 'archived'])
    exclude_list_names = filter_settings.get('exclude_list_names', ['managex', 'template', 'archived'])
    
    logger.info(f"🔧 Using filters - Include folders: {include_folders}")
    logger.info(f"🚫 Exclude folders: {exclude_folders}")
    logger.info(f"🚫 Exclude list names: {exclude_list_names}")
    
    try:
        # Get all spaces for the team
        spaces_url = f"https://api.clickup.com/api/v2/team/{team_id}/space"
        logger.debug(f"🌐 Fetching spaces: {spaces_url}")
        
        response = requests.get(spaces_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        spaces = response.json().get("spaces", [])
        logger.info(f"📂 Found {len(spaces)} spaces")
        
        sprint_lists = []
        
        for space in spaces:
            space_id = space.get("id")
            space_name = space.get("name", "Unknown Space")
            
            # Check if space should be excluded
            if should_exclude_by_name(space_name, exclude_folders):
                logger.info(f"🚫 Excluding space: '{space_name}'")
                continue
            
            # Get folders in this space
            folders_url = f"https://api.clickup.com/api/v2/space/{space_id}/folder"
            logger.debug(f"📁 Fetching folders for space '{space_name}': {folders_url}")
            
            try:
                folder_response = requests.get(folders_url, headers=headers, timeout=30)
                folder_response.raise_for_status()
                
                folders = folder_response.json().get("folders", [])
                
                for folder in folders:
                    folder_id = folder.get("id")
                    folder_name = folder.get("name", "")
                    
                    # Check if folder should be excluded
                    if should_exclude_by_name(folder_name, exclude_folders):
                        logger.debug(f"🚫 Excluding folder: '{folder_name}'")
                        continue
                    
                    # Check if this looks like a sprint folder
                    if is_sprint_folder(folder_name):
                        # Get lists in this folder
                        lists_url = f"https://api.clickup.com/api/v2/folder/{folder_id}/list"
                        
                        try:
                            lists_response = requests.get(lists_url, headers=headers, timeout=30)
                            lists_response.raise_for_status()
                            
                            lists = lists_response.json().get("lists", [])
                            
                            for list_item in lists:
                                list_name = list_item.get('name', '')
                                full_list_name = f"{space_name} - {folder_name} - {list_name}"
                                
                                # Check if list should be excluded
                                if should_exclude_by_name(full_list_name, exclude_list_names):
                                    logger.debug(f"🚫 Excluding list: '{full_list_name}'")
                                    continue
                                
                                sprint_lists.append({
                                    "id": list_item.get("id"),
                                    "name": full_list_name,
                                    "type": "sprint",
                                    "enabled": True,
                                    "space": space_name,
                                    "folder": folder_name,
                                    "discovered": True,
                                    "discovery_date": datetime.now().isoformat()
                                })
                                logger.debug(f"✅ Added sprint list: '{full_list_name}'")
                                
                        except Exception as e:
                            logger.warning(f"⚠️  Failed to get lists from folder '{folder_name}': {e}")
                            
            except Exception as e:
                logger.warning(f"⚠️  Failed to get folders from space '{space_name}': {e}")
                
        logger.info(f"🎯 Discovered {len(sprint_lists)} sprint lists (after filtering)")
        return sprint_lists
        
    except Exception as e:
        logger.error(f"❌ Failed to discover sprints: {e}")
        return []

def should_exclude_by_name(name: str, exclude_patterns: List[str]) -> bool:
    """Check if a name should be excluded based on patterns"""
    name_lower = name.lower()
    for pattern in exclude_patterns:
        if pattern.lower() in name_lower:
            return True
    return False

def is_sprint_folder(folder_name: str) -> bool:
    """Check if a folder name indicates it's a sprint folder"""
    sprint_indicators = [
        "sprint", "iteration", "pi ", "program increment",
        "release", "milestone", "cycle", "wave"
    ]
    
    folder_lower = folder_name.lower()
    return any(indicator in folder_lower for indicator in sprint_indicators)

def update_config_with_discovered_lists(discovered_lists: List[Dict]):
    """Update configuration with newly discovered lists"""
    config_file = os.getenv('CLICKUP_CONFIG_FILE', 'clickup_config.json')
    
    try:
        # Load existing config
        existing_config = {"lists": []}
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                existing_config = json.load(f)
        
        existing_list_ids = {item["id"] for item in existing_config.get("lists", [])}
        
        # Add new discovered lists
        new_lists = []
        for discovered_list in discovered_lists:
            if discovered_list["id"] not in existing_list_ids:
                new_lists.append(discovered_list)
                existing_config["lists"].append(discovered_list)
        
        if new_lists:
            # Save updated config
            with open(config_file, 'w') as f:
                json.dump(existing_config, f, indent=2)
            
            logger.info(f"📝 Added {len(new_lists)} new lists to configuration")
            for new_list in new_lists:
                logger.info(f"   ➕ {new_list['name']} ({new_list['type']})")
        else:
            logger.info("✅ No new lists to add")
            
    except Exception as e:
        logger.error(f"❌ Failed to update configuration: {e}")

def fetch_tasks():
    """Fetch tasks from all configured ClickUp lists and categorize them by status"""
    logger.info("🔍 Starting multi-list task fetch from ClickUp")
    
    # Validate API key
    api_key = os.getenv("CLICKUP_API_KEY")
    if not api_key:
        logger.error("❌ Missing ClickUp API key")
        raise ValueError("Missing CLICKUP_API_KEY environment variable")
    
    # Auto-discover sprints if team ID is provided
    team_id = os.getenv("CLICKUP_TEAM_ID")
    if team_id:
        logger.info(f"🔄 Auto-discovering sprints for team: {team_id}")
        discovered_lists = discover_sprints(team_id, api_key)
        if discovered_lists:
            update_config_with_discovered_lists(discovered_lists)
    
    # Get list configuration
    try:
        list_configs = get_list_config()
        enabled_lists = [config for config in list_configs if config.get("enabled", True)]
        logger.info(f"📋 Found {len(enabled_lists)} enabled lists to process")
    except Exception as e:
        logger.error(f"❌ Failed to get list configuration: {e}")
        raise
    
    if not enabled_lists:
        logger.warning("⚠️  No enabled lists found")
        return []
    
    all_tasks = []
    
    # Process each list
    for list_config in enabled_lists:
        list_id = list_config["id"]
        list_name = list_config.get("name", f"List {list_id}")
        list_type = list_config.get("type", "general")
        
        logger.info(f"📋 Processing list: '{list_name}' ({list_type})")
        
        try:
            tasks = fetch_tasks_from_list(list_id, list_name, list_type, api_key)
            all_tasks.extend(tasks)
            logger.info(f"✅ Retrieved {len(tasks)} relevant tasks from '{list_name}'")
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch tasks from '{list_name}': {e}")
            continue
    
    logger.info(f"🎯 Total tasks to process across all lists: {len(all_tasks)}")
    return all_tasks

def fetch_tasks_from_list(list_id: str, list_name: str, list_type: str, api_key: str) -> List[Tuple]:
    """Fetch and categorize tasks from a specific ClickUp list"""
    
    headers = {"Authorization": api_key}
    url = f"https://api.clickup.com/api/v2/list/{list_id}/task"
    
    try:
        logger.debug(f"🔗 Calling ClickUp API for '{list_name}': {url}")
        response = requests.get(url, headers=headers, timeout=30)
        logger.debug(f"📡 API Response Status: {response.status_code}")
        response.raise_for_status()
        
        raw_data = response.json()
        tasks = raw_data.get("tasks", [])
        logger.debug(f"📥 Retrieved {len(tasks)} raw tasks from '{list_name}'")
        
        if not tasks:
            return []
        
    except requests.exceptions.Timeout:
        logger.error(f"⏱️  ClickUp API request timed out for '{list_name}'")
        raise
    except requests.exceptions.HTTPError as e:
        logger.error(f"🚫 ClickUp API HTTP error for '{list_name}': {response.status_code} - {str(e)}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"🌐 Network error fetching tasks from '{list_name}': {str(e)}")
        raise

    # Process and categorize tasks
    result = []
    today = datetime.today().date()
    now = datetime.now()
    twenty_four_hours_ago = now - timedelta(hours=24)
    
    # Counters for logging
    status_counts = {
        "completed": 0,
        "due_today": 0,
        "overdue": 0,
        "unassigned": 0,
        "no_due_date": 0,
        "skipped": 0
    }

    for i, task in enumerate(tasks, 1):
        task_id = task.get("id", "unknown")
        name = task.get("name", "Unnamed Task")
        status = task.get("status", {}).get("status", "unknown")
        due = task.get("due_date")
        assignees = task.get("assignees", [])
        date_closed = task.get("date_closed")  # When task was completed
        
        # Handle multiple assignees - extract usernames
        assignee_names = []
        if assignees:
            for assignee in assignees:
                username = assignee.get("username")
                if username:
                    assignee_names.append(username)
        
        # Use list of assignees or None if empty
        users = assignee_names if assignee_names else None
        
        logger.debug(f"📋 Processing task {i}/{len(tasks)}: '{name}' (ID: {task_id}, Assignees: {users})")

        # Categorize tasks with list context - now including task_id and multiple assignees
        if not users:
            result.append((name, task_id, [], "unassigned", list_name, list_type))
            status_counts["unassigned"] += 1
        elif not due and status != "complete":
            result.append((name, task_id, users, "no_due_date", list_name, list_type))
            status_counts["no_due_date"] += 1
        elif status == "complete":
            # Check if task was completed in the last 24 hours
            if date_closed:
                try:
                    # Convert ClickUp timestamp to datetime
                    completed_date = datetime.fromtimestamp(int(date_closed) / 1000)
                    
                    if completed_date >= twenty_four_hours_ago:
                        # Task completed in last 24 hours - send appreciation
                        result.append((name, task_id, users, "completed", list_name, list_type))
                        status_counts["completed"] += 1
                        logger.debug(f"✅ Task '{name}' completed recently: {completed_date.strftime('%Y-%m-%d %H:%M')}")
                    else:
                        # Task completed more than 24 hours ago - skip
                        status_counts["skipped"] += 1
                        logger.debug(f"⏭️  Task '{name}' completed too long ago: {completed_date.strftime('%Y-%m-%d %H:%M')}")
                        
                except (ValueError, TypeError) as e:
                    logger.warning(f"⚠️  Invalid completion date for task '{name}': {date_closed} - {str(e)}")
                    status_counts["skipped"] += 1
            else:
                # No completion date available - skip
                status_counts["skipped"] += 1
                logger.debug(f"⏭️  Task '{name}' has no completion date")
        elif due:
            try:
                due_date = datetime.fromtimestamp(int(due) / 1000).date()
                
                if due_date == today:
                    result.append((name, task_id, users, "due_today", list_name, list_type))
                    status_counts["due_today"] += 1
                elif due_date < today:
                    # Calculate how many days overdue
                    days_overdue = (today - due_date).days
                    overdue_status = f"overdue_{days_overdue}"
                    result.append((name, task_id, users, overdue_status, list_name, list_type))
                    status_counts["overdue"] += 1
                    logger.debug(f"🚨 Task '{name}' is {days_overdue} days overdue")
                else:
                    status_counts["skipped"] += 1
            except (ValueError, TypeError) as e:
                logger.warning(f"⚠️  Invalid due date format for task '{name}': {due} - {str(e)}")
                status_counts["skipped"] += 1
        else:
            status_counts["skipped"] += 1

    # Log summary for this list
    logger.info(f"📊 '{list_name}' ({list_type}) summary:")
    if sum(status_counts.values()) > 0:
        logger.info(f"   ✅ Completed: {status_counts['completed']}")
        logger.info(f"   📅 Due Today: {status_counts['due_today']}")
        logger.info(f"   🚨 Overdue: {status_counts['overdue']}")
        logger.info(f"   👥 Unassigned: {status_counts['unassigned']}")
        logger.info(f"   📝 No Due Date: {status_counts['no_due_date']}")

    return result 