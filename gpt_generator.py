import logging
import json
import os
from openai import OpenAI

logger = logging.getLogger(__name__)

def load_user_mappings():
    """Load user mappings from configuration file"""
    mapping_file = os.getenv('USER_MAPPING_FILE', 'user_mapping.json')
    
    if os.path.exists(mapping_file):
        try:
            with open(mapping_file, 'r') as f:
                config = json.load(f)
                logger.debug(f"📋 Loaded user mappings from {mapping_file}")
                return config
        except Exception as e:
            logger.warning(f"⚠️  Failed to load user mappings: {e}")
    
    # Default configuration if file doesn't exist
    return {
        "user_mappings": {},
        "default_mention": "@channel",
        "fallback_behavior": "use_clickup_name"
    }

def get_slack_username(clickup_user):
    """Convert ClickUp username to Slack user ID format <@user_id>"""
    if not clickup_user or clickup_user == "everyone":
        return "@channel"
    
    # Load user mappings
    config = load_user_mappings()
    user_mappings = config.get("user_mappings", {})
    fallback_behavior = config.get("fallback_behavior", "use_clickup_name")
    default_mention = config.get("default_mention", "@channel")
    
    # Check if mapping exists
    if clickup_user in user_mappings:
        slack_user_id = user_mappings[clickup_user]
        # Check if it's a Slack user ID (starts with U)
        if slack_user_id.startswith('U'):
            slack_mention = f"<@{slack_user_id}>"
            logger.debug(f"👤 Mapped '{clickup_user}' → '{slack_mention}'")
            return slack_mention
        else:
            # Legacy format - display name
            logger.debug(f"👤 Mapped '{clickup_user}' → '@{slack_user_id}'")
            return f"@{slack_user_id}"
    
    # Handle fallback behavior
    if fallback_behavior == "use_clickup_name":
        logger.debug(f"👤 No mapping found, using ClickUp name: '{clickup_user}' (untagged)")
        return clickup_user  # Return plain text without @
    elif fallback_behavior == "use_default":
        logger.debug(f"👤 No mapping found, using default: '{default_mention}'")
        return default_mention
    else:
        logger.debug(f"👤 No mapping found, using @channel as fallback")
        return "@channel"

def get_slack_usernames(assignees):
    """Convert multiple ClickUp usernames to Slack user ID format"""
    if not assignees:
        return "@channel"
    
    # Handle single assignee
    if isinstance(assignees, str):
        return get_slack_username(assignees)
    
    # Handle multiple assignees
    if isinstance(assignees, list):
        mentions = []
        for assignee in assignees:
            mention = get_slack_username(assignee)
            if mention not in mentions:  # Avoid duplicates
                mentions.append(mention)
        
        if len(mentions) == 1:
            return mentions[0]
        elif len(mentions) == 2:
            return f"{mentions[0]} and {mentions[1]}"
        else:
            return ", ".join(mentions[:-1]) + f", and {mentions[-1]}"
    
    return "@channel"

def generate_message(task_name, task_id, assignees, status, api_key, list_name=None, list_type=None):
    """Generate a funny message with task ID, name, and multiple assignees"""
    logger.info(f"🤖 Generating message for task: '{task_name}' (ID: {task_id}, Status: {status}, Assignees: {assignees})")
    
    if not api_key:
        logger.error("❌ Missing OpenAI API key")
        raise ValueError("Missing OPENAI_API_KEY environment variable")
    
    logger.debug(f"🔑 OpenAI API key present: {api_key[:10]}...")
    
    client = OpenAI(api_key=api_key)

    # Get Slack mentions for assignees
    user_mentions = get_slack_usernames(assignees)
    
    # Check if CEO is in assignees (U03MNP6KBQC - Dinesh Kumar)
    ceo_user_id = "U03MNP6KBQC"
    is_ceo_task = any(assignee for assignee in assignees if get_slack_username(assignee) == f"<@{ceo_user_id}>")
    
    # Handle different overdue levels
    if status.startswith("overdue_"):
        days_overdue = int(status.split("_")[1])
        return generate_overdue_message(task_name, task_id, user_mentions, days_overdue, is_ceo_task, api_key)
    
    # Simple English prompts with task context - now including task name for contextual humor
    prompts = {
        "completed": f"Write a short funny message (max 15 words) praising {user_mentions} for finishing the task '{task_name}'. Use very simple words like a 5-year-old would understand. Make it about the task. Add 1 emoji.",
        "due_today": f"Write a short funny reminder (max 15 words) telling {user_mentions} that their task '{task_name}' is due today. Use very simple words like talking to a friend. Make it about the task. Add 1 emoji.",
        "overdue": f"Write a short funny message (max 15 words) telling {user_mentions} that their task '{task_name}' is late. Use very simple words, be nice and friendly. Make it about the task. Add 1 emoji.",
        "unassigned": f"Write a short funny message (max 15 words) asking who wants to take the task '{task_name}'. Use very simple words like talking to friends. Make it about the task. Add 1 emoji.",
        "no_due_date": f"Write a short funny message (max 15 words) about {user_mentions}'s task '{task_name}' having no due date. Use very simple words everyone knows. Make it about the task. Add 1 emoji.",
    }

    if status not in prompts:
        logger.error(f"❌ Unknown status type: {status}")
        raise ValueError(f"Unknown status type: {status}")
    
    prompt = prompts[status]
    logger.debug(f"📝 Using prompt: {prompt[:150]}...")

    try:
        logger.info("🔮 Calling OpenAI GPT-4 API...")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{
                "role": "system", 
                "content": "You write short, funny messages using very simple English. Use words that a 5-year-old can understand. No big words, no jargon, no technical terms. Talk like you're chatting with friends. Be funny but keep it simple and friendly."
            }, {
                "role": "user", 
                "content": prompt
            }],
            temperature=0.7,
            max_tokens=80  # Even shorter for simpler messages
        )
        
        logger.debug(f"📊 OpenAI API response received")
        
        generated_humor = response.choices[0].message.content.strip()
        
        # Create message with humor first, then task info on next line
        full_message = f"{generated_humor}\n{task_id}: {task_name}"
        
        logger.info(f"✅ Successfully generated message via OpenAI")
        logger.debug(f"📄 Generated message: {full_message}")
        
        return full_message
        
    except Exception as e:
        logger.error(f"❌ Error generating message with OpenAI: {str(e)}")
        logger.info("🔄 Falling back to predefined messages")
        
        # Fallback with humor first, then task info
        fallback_humor = get_fallback_message(task_name, assignees, status)
        full_message = f"{fallback_humor}\n{task_id}: {task_name}"
        logger.info(f"🔄 Using fallback message: {full_message}")
        return full_message

def generate_overdue_message(task_name, task_id, user_mentions, days_overdue, is_ceo_task, api_key):
    """Generate overdue messages with increasing scolding levels, but always funny for CEO"""
    
    if is_ceo_task:
        # Always funny for CEO, no matter how overdue
        ceo_prompts = [
            f"Write a funny message (max 15 words) about the CEO being {days_overdue} days late on '{task_name}'. Be playful and respectful, like joking with your boss. Use simple words. Add 1 emoji.",
            f"Write a funny message (max 15 words) about the boss taking {days_overdue} days extra on '{task_name}'. Be funny but respectful. Use simple words. Add 1 emoji.",
            f"Write a funny message (max 15 words) about the CEO's '{task_name}' being {days_overdue} days overdue. Make it funny and nice. Use simple words. Add 1 emoji."
        ]
        prompt = ceo_prompts[min(days_overdue - 1, 2)]  # Use different prompts but all funny
        
    else:
        # Regular employees - funny for first 2 days, then scolding from day 3
        if days_overdue <= 2:
            prompt = f"Write a funny message (max 15 words) that {user_mentions}'s task '{task_name}' is {days_overdue} days late. Keep it light and funny. Use simple words. Add 1 emoji."
        elif days_overdue <= 5:
            prompt = f"Write a firmer reminder (max 15 words) that {user_mentions}'s task '{task_name}' is {days_overdue} days late. Be more serious but not mean. Use simple words. Add 1 emoji."
        elif days_overdue <= 10:
            prompt = f"Write a serious message (max 15 words) that {user_mentions}'s task '{task_name}' is {days_overdue} days late. Be firm and direct. Use simple words. Add 1 emoji."
        else:
            prompt = f"Write a very serious message (max 15 words) that {user_mentions}'s task '{task_name}' is {days_overdue} days late. Be stern but professional. Use simple words. Add 1 emoji."
    
    try:
        client = OpenAI(api_key=api_key)
        
        system_content = "You write messages using very simple English. Use words that a 5-year-old can understand. No big words, no jargon, no technical terms."
        if is_ceo_task:
            system_content += " Always be respectful and funny when talking about the CEO/boss."
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{
                "role": "system", 
                "content": system_content
            }, {
                "role": "user", 
                "content": prompt
            }],
            temperature=0.7,
            max_tokens=80
        )
        
        generated_humor = response.choices[0].message.content.strip()
        full_message = f"{generated_humor}\n{task_id}: {task_name}"
        
        return full_message
        
    except Exception as e:
        logger.error(f"❌ Error generating overdue message: {str(e)}")
        
        # Fallback overdue messages
        if is_ceo_task:
            fallback_humor = get_ceo_overdue_fallback(user_mentions, days_overdue)
        else:
            fallback_humor = get_overdue_fallback(user_mentions, days_overdue)
        
        return f"{fallback_humor}\n{task_id}: {task_name}"

def get_ceo_overdue_fallback(user_mentions, days_overdue):
    """Funny fallback messages for CEO, always respectful"""
    ceo_messages = [
        f"😄 {user_mentions}, even the best boss needs a little nudge sometimes! {days_overdue} days and counting!",
        f"🎩 {user_mentions}, your task is taking a little vacation! {days_overdue} days of fun!",
        f"👑 {user_mentions}, even kings take their time! {days_overdue} days of royal delay!",
        f"🌟 {user_mentions}, your task is aging like fine wine! {days_overdue} days of perfection!",
        f"🚀 {user_mentions}, slow and steady wins the race! {days_overdue} days of careful thinking!"
    ]
    
    # Cycle through messages for different days
    message_index = min(days_overdue - 1, len(ceo_messages) - 1)
    return ceo_messages[message_index]

def get_overdue_fallback(user_mentions, days_overdue):
    """Escalating fallback messages for regular employees - funny first 2 days, then scolding"""
    if days_overdue <= 2:
        funny_messages = [
            f"😄 {user_mentions}, your task is taking a little nap! {days_overdue} days of rest!",
            f"🐌 {user_mentions}, your task is moving like a snail! {days_overdue} days slow!",
            f"🎈 {user_mentions}, your task is floating away! {days_overdue} days in the air!"
        ]
        message_index = min(days_overdue - 1, len(funny_messages) - 1)
        return funny_messages[message_index]
    elif days_overdue <= 5:
        return f"🔔 {user_mentions}, {days_overdue} days late now. Time to catch up!"
    elif days_overdue <= 10:
        return f"🚨 {user_mentions}, this is {days_overdue} days late. Please finish it soon!"
    else:
        return f"⚠️ {user_mentions}, {days_overdue} days late is too much. We need this done now!"

def get_fallback_message(task_name, assignees, status):
    """Generate contextual fallback messages based on task name when OpenAI is unavailable"""
    
    # Get Slack mentions for assignees
    user_mentions = get_slack_usernames(assignees)
    
    # Simple task type detection for contextual humor
    task_lower = task_name.lower()
    
    # Detect task types for contextual messages
    if any(word in task_lower for word in ['bug', 'fix', 'error', 'issue', 'broken']):
        task_type = 'bug'
    elif any(word in task_lower for word in ['test', 'testing', 'qa', 'quality']):
        task_type = 'test'
    elif any(word in task_lower for word in ['design', 'ui', 'ux', 'interface', 'mockup']):
        task_type = 'design'
    elif any(word in task_lower for word in ['api', 'endpoint', 'service', 'backend']):
        task_type = 'api'
    elif any(word in task_lower for word in ['database', 'db', 'query', 'sql']):
        task_type = 'database'
    elif any(word in task_lower for word in ['deploy', 'release', 'production', 'launch']):
        task_type = 'deploy'
    elif any(word in task_lower for word in ['document', 'docs', 'readme', 'guide']):
        task_type = 'docs'
    elif any(word in task_lower for word in ['meeting', 'call', 'discuss', 'review']):
        task_type = 'meeting'
    else:
        task_type = 'general'
    
    # Contextual fallback messages based on task type and status
    contextual_messages = {
        "completed": {
            'bug': f"🐛 {user_mentions} fixed that bug! Nice work!",
            'test': f"✅ {user_mentions} tested it! All good!",
            'design': f"🎨 {user_mentions} made it look great!",
            'api': f"🔌 {user_mentions} connected it! Works now!",
            'database': f"💾 {user_mentions} organized the data! Clean!",
            'deploy': f"🚀 {user_mentions} put it live! Success!",
            'docs': f"📚 {user_mentions} wrote it down! Clear!",
            'meeting': f"🤝 {user_mentions} had the meeting! Done!",
            'general': f"🎉 Great job {user_mentions}! Task done!"
        },
        "due_today": {
            'bug': f"🐛 Hey {user_mentions}, fix that bug today!",
            'test': f"🧪 Hey {user_mentions}, test it today!",
            'design': f"🎨 Hey {user_mentions}, make it pretty today!",
            'api': f"🔌 Hey {user_mentions}, connect it today!",
            'database': f"💾 Hey {user_mentions}, organize data today!",
            'deploy': f"🚀 Hey {user_mentions}, put it live today!",
            'docs': f"📚 Hey {user_mentions}, write it today!",
            'meeting': f"🤝 Hey {user_mentions}, meeting today!",
            'general': f"⏰ Hey {user_mentions}, task due today!"
        },
        "overdue": {
            'bug': f"🐛 {user_mentions}, that bug is still there!",
            'test': f"🧪 {user_mentions}, still need to test it!",
            'design': f"🎨 {user_mentions}, still need to design it!",
            'api': f"🔌 {user_mentions}, still need to connect it!",
            'database': f"💾 {user_mentions}, data still messy!",
            'deploy': f"🚀 {user_mentions}, still need to put it live!",
            'docs': f"📚 {user_mentions}, still need to write it!",
            'meeting': f"🤝 {user_mentions}, still need that meeting!",
            'general': f"🚨 {user_mentions}, task is late!"
        },
        "unassigned": {
            'bug': f"🐛 Who wants to fix this bug?",
            'test': f"🧪 Who wants to test this?",
            'design': f"🎨 Who wants to design this?",
            'api': f"🔌 Who wants to connect this?",
            'database': f"💾 Who wants to organize data?",
            'deploy': f"🚀 Who wants to put this live?",
            'docs': f"📚 Who wants to write this?",
            'meeting': f"🤝 Who wants to join this meeting?",
            'general': f"🤷 Who wants this task?"
        },
        "no_due_date": {
            'bug': f"🐛 {user_mentions}, when will you fix this bug?",
            'test': f"🧪 {user_mentions}, when will you test this?",
            'design': f"🎨 {user_mentions}, when will you design this?",
            'api': f"🔌 {user_mentions}, when will you connect this?",
            'database': f"💾 {user_mentions}, when will you organize this?",
            'deploy': f"🚀 {user_mentions}, when will you put this live?",
            'docs': f"📚 {user_mentions}, when will you write this?",
            'meeting': f"🤝 {user_mentions}, when is this meeting?",
            'general': f"📅 {user_mentions}, when is this due?"
        }
    }
    
    return contextual_messages.get(status, {}).get(task_type, f"Task update for {user_mentions}")

def get_list_context(list_type, list_name):
    """Get context information based on list type for more targeted messaging"""
    
    contexts = {
        "sprint": {
            "item_type": "task",
            "list_description": f"Sprint" if list_name else "sprint",
        },
        "feature": {
            "item_type": "feature",
            "list_description": f"Features" if list_name else "features",
        },
        "bug": {
            "item_type": "bug",
            "list_description": f"Bugs" if list_name else "bugs",
        },
        "general": {
            "item_type": "task",
            "list_description": f"Tasks" if list_name else "tasks",
        }
    }
    
    return contexts.get(list_type, contexts["general"]) 