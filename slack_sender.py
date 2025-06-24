import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os

logger = logging.getLogger(__name__)

def send_to_slack(message):
    """Send a message to the configured Slack channel"""
    logger.info("💬 Preparing to send message to Slack")
    logger.debug(f"📝 Message content: {message}")
    
    bot_token = os.getenv("SLACK_BOT_TOKEN")
    channel_id = os.getenv("SLACK_CHANNEL_ID")
    
    if not bot_token or not channel_id:
        logger.error("❌ Missing Slack credentials")
        raise ValueError("Missing SLACK_BOT_TOKEN or SLACK_CHANNEL_ID environment variables")
    
    logger.debug(f"🔑 Using Slack channel: {channel_id}")
    logger.debug(f"🔑 Bot token present: {bot_token[:15]}...")
    
    client = WebClient(token=bot_token)
    
    try:
        logger.info(f"🚀 Sending message to Slack channel {channel_id}")
        response = client.chat_postMessage(
            channel=channel_id,
            text=message,
            unfurl_links=False,
            unfurl_media=False
        )
        
        logger.debug(f"📡 Slack API response: {response}")
        
        if response["ok"]:
            message_ts = response.get("ts", "unknown")
            logger.info(f"✅ Message sent successfully to Slack (timestamp: {message_ts})")
            logger.debug(f"📊 Message details: Channel={response.get('channel')}, TS={message_ts}")
        else:
            error_msg = response.get('error', 'Unknown error')
            logger.error(f"❌ Failed to send message: {error_msg}")
            raise SlackApiError(f"Slack API returned error: {error_msg}", response)
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        logger.error(f"❌ Slack API error: {error_code}")
        
        # Provide more specific error information
        if error_code == 'channel_not_found':
            logger.error("🔍 Channel not found - check your SLACK_CHANNEL_ID")
        elif error_code == 'not_in_channel':
            logger.error("🚫 Bot is not in the channel - invite the bot to the channel")
        elif error_code == 'invalid_auth':
            logger.error("🔐 Invalid authentication - check your SLACK_BOT_TOKEN")
        elif error_code == 'missing_scope':
            logger.error("🔒 Missing required OAuth scopes - check bot permissions")
        elif error_code == 'rate_limited':
            logger.error("⏱️  Rate limited by Slack API - wait before retrying")
        
        raise
    except Exception as e:
        logger.error(f"💥 Unexpected error sending to Slack: {str(e)}")
        logger.debug(f"Exception type: {type(e).__name__}")
        raise 