from dotenv import load_dotenv
import os
import logging
import time
import random
from datetime import datetime
from clickup_fetcher import fetch_tasks
from gpt_generator import generate_message
from slack_sender import send_to_slack

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('clickup_bot.log')
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

def run_bot():
    """Main function to run the ClickUp reminder bot"""
    logger.info("🚀 Starting ClickUp Reminder Bot")
    logger.info(f"⏰ Execution time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if today is a weekday (Monday=0, Sunday=6)
    today = datetime.now().weekday()
    if today >= 5:  # Saturday=5, Sunday=6
        day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][today]
        logger.info(f"🏖️ It's {day_name}! Skipping reminder bot execution on weekends.")
        logger.info("💤 See you on Monday! Have a great weekend!")
        return
    
    try:
        # Validate environment variables
        required_vars = ['OPENAI_API_KEY', 'SLACK_BOT_TOKEN', 'SLACK_CHANNEL_ID', 'CLICKUP_API_KEY']
        optional_vars = ['CLICKUP_LIST_ID', 'CLICKUP_TEAM_ID', 'CLICKUP_CONFIG_FILE']
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            raise ValueError(f"Missing environment variables: {', '.join(missing_vars)}")
        
        logger.info("✅ All required environment variables validated")
        
        # Log optional configuration
        for var in optional_vars:
            value = os.getenv(var)
            if value:
                logger.info(f"🔧 Optional config - {var}: {'***' if 'key' in var.lower() else value}")
        
        # Fetch tasks
        logger.info("🔄 Fetching tasks from ClickUp...")
        tasks = fetch_tasks()
        
        if not tasks:
            logger.info("✅ No tasks to process today!")
            return
            
        logger.info(f"📋 Found {len(tasks)} tasks to process across all lists")
        
        # Process each task
        successful_messages = 0
        failed_messages = 0
        
        for i, task_data in enumerate(tasks, 1):
            # New format: (task_name, task_id, assignees, status, list_name, list_type)
            if len(task_data) == 6:
                task_name, task_id, assignees, status, list_name, list_type = task_data
            elif len(task_data) == 5:
                # Backward compatibility - old format
                task_name, user, status, list_name, list_type = task_data
                task_id = "unknown"
                assignees = [user] if user and user != "everyone" else []
            else:
                # Very old format
                task_name, user, status = task_data[:3]
                task_id = "unknown"
                assignees = [user] if user and user != "everyone" else []
                list_name = "Default List"
                list_type = "general"
            
            # Format assignees for logging
            assignee_display = ", ".join(assignees) if assignees else "Unassigned"
            logger.info(f"📝 Processing task {i}/{len(tasks)}: '{task_name}' (ID: {task_id}, Status: {status}, Assignees: {assignee_display}, List: {list_name})")
            
            try:
                # Generate message with task ID and multiple assignees
                logger.debug(f"🤖 Generating message for task: {task_name}")
                message = generate_message(
                    task_name, task_id, assignees, status, 
                    os.getenv("OPENAI_API_KEY"), 
                    list_name, list_type
                )
                logger.info(f"💭 Generated message: {message[:100]}{'...' if len(message) > 100 else ''}")
                
                # Send to Slack
                logger.debug(f"💬 Sending message to Slack...")
                send_to_slack(message)
                successful_messages += 1
                logger.info(f"✅ Successfully processed task {i}/{len(tasks)}")
                
                # Add 3-minute delay between messages to avoid spamming
                if i < len(tasks):  # Don't delay after the last message
                    delay_minutes = 3
                    delay_seconds = delay_minutes * 60
                    logger.info(f"⏱️  Waiting {delay_minutes} minutes before next message...")
                    time.sleep(delay_seconds)
                
            except Exception as e:
                failed_messages += 1
                logger.error(f"❌ Failed to process task '{task_name}': {str(e)}")
                continue
                
        # Summary
        logger.info(f"🎉 Bot execution completed!")
        logger.info(f"📊 Summary: {successful_messages} successful, {failed_messages} failed out of {len(tasks)} total tasks")
        
        if failed_messages > 0:
            logger.warning(f"⚠️  {failed_messages} tasks failed to process - check logs above for details")
        
    except Exception as e:
        logger.error(f"💥 Critical error running bot: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    run_bot() 