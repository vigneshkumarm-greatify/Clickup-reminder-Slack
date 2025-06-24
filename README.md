# 🎯 ClickUp Reminder Bot

A Python bot that fetches tasks from ClickUp, generates funny AI-powered messages, and posts them to Slack. Perfect for keeping your team motivated and informed about task statuses!

## 🚀 Features

- **Multi-List Support**: Track tasks across multiple ClickUp lists (sprints, features, bugs, etc.)
- **Auto-Sprint Discovery**: Automatically discovers and tracks new sprint lists
- **Context-Aware Messaging**: Different message styles for different list types
- **Task Status Monitoring**: Tracks completed, due today, overdue, unassigned, and no due date tasks
- **AI-Powered Messages**: Uses GPT-4 to generate funny, contextual messages
- **Slack Integration**: Automatically posts messages to your team channel
- **Automated Scheduling**: Runs daily via cron on Railway
- **Configuration Management**: Easy-to-use utility for managing lists
- **Error Handling**: Robust error handling with fallback messages
- **User Mapping**: Maps ClickUp usernames to Slack usernames

## 📦 Project Structure

```
clickup-reminder-bot/
├── main.py                      # Main orchestrator
├── clickup_fetcher.py           # ClickUp API integration (multi-list support)
├── gpt_generator.py             # OpenAI message generation (context-aware)
├── slack_sender.py              # Slack message posting
├── manage_lists.py              # List management utility
├── clickup_config.example.json  # Multi-list configuration example
├── env.example                  # Environment variables template
├── requirements.txt             # Python dependencies
└── README.md                   # This file
```

## 🛠️ Setup Instructions

### 1. Clone and Install Dependencies

```bash
git clone <your-repo-url>
cd clickup-reminder-bot
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```env
OPENAI_API_KEY=sk-your-openai-key
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_CHANNEL_ID=C1234567890
CLICKUP_API_KEY=pk_your-clickup-key
CLICKUP_LIST_ID=12345678
USER_MAPPING_FILE=user_mapping.json
```

### 3. API Keys Setup

#### OpenAI API Key
1. Go to [OpenAI API](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add it to your `.env` file

#### Slack Bot Token
1. Go to [Slack API](https://api.slack.com/apps)
2. Create a new app or use existing one
3. Go to "OAuth & Permissions"
4. Add these scopes: `chat:write`, `chat:write.public`
5. Install app to workspace
6. Copy the "Bot User OAuth Token" (starts with `xoxb-`)

#### Slack Channel ID
1. Open Slack in browser
2. Navigate to your target channel
3. Copy the channel ID from the URL (e.g., `/messages/C1234567890/`)

#### ClickUp API
1. Go to ClickUp → Settings → Apps
2. Generate a Personal API Token
3. Get your Team ID from ClickUp URL (clickup.com/[TEAM_ID]/...)
4. Find List IDs from ClickUp URLs when viewing lists

**For Multi-List Setup:**
- Set `CLICKUP_TEAM_ID` for auto-discovery
- Use the configuration file approach (recommended)

**For Single List Setup:**
- Set `CLICKUP_LIST_ID` for backward compatibility

### 4. Test Locally

```bash
python main.py
```

The bot will create a log file `clickup_bot.log` in the same directory and also output logs to the console.

## 🎯 Multi-List Configuration

The bot supports tracking multiple ClickUp lists with different purposes:

### Configuration Methods

#### Method 1: Single List (Backward Compatible)
Set `CLICKUP_LIST_ID` in your `.env` file for a single list.

#### Method 2: Multi-List with Configuration File (Recommended)
1. Copy `clickup_config.example.json` to `clickup_config.json`
2. Configure your lists:

```json
{
  "lists": [
    {
      "id": "123456789",
      "name": "Sprint 24 - Q4 Development",
      "type": "sprint",
      "enabled": true
    },
    {
      "id": "987654321",
      "name": "Bug Tracker",
      "type": "bug",
      "enabled": true
    }
  ]
}
```

### List Types & Message Styles

- **`sprint`**: Sprint/iteration tasks with agile terminology
- **`feature`**: Feature development with user impact focus
- **`bug`**: Bug tracking with stability messaging
- **`general`**: General tasks with standard messaging

### Auto-Discovery of New Sprints

Set `CLICKUP_TEAM_ID` to automatically discover new sprint lists:

```bash
# Run discovery manually
python manage_lists.py --discover

# Or use interactive mode
python manage_lists.py
```

### Managing Lists

Use the included utility to manage your configuration:

```bash
# Interactive management
python manage_lists.py

# Command line options
python manage_lists.py --list           # Show current config
python manage_lists.py --discover       # Find new sprints
python manage_lists.py --toggle         # Enable/disable lists
python manage_lists.py --add            # Add new list manually
```

### Sample Messages by List Type

**Sprint Tasks:**
- ✅ "🚀 @john just crushed that sprint task 'User Authentication'! Sprint velocity is through the roof!"
- ⏰ "Hey @sarah, 'API Integration' is due today. Don't let it block the standup! ⚡"

**Bug Reports:**
- 🚨 "@mike, that bug 'Login Issue' is overdue. Users are probably doing the confused face emoji! 🐛"

**Features:**
- 🎉 "@alex completed the feature 'Dark Mode'! Users are going to love this! ✨"

## 🌐 Railway Deployment

### 1. Prepare for Deployment

1. Push your code to GitHub (make sure `.env` is in `.gitignore`)
2. Go to [Railway](https://railway.app)
3. Click "New Project" → "Deploy from GitHub"
4. Select your repository

### 2. Environment Variables

In Railway dashboard, go to your project and add these environment variables:

**Required:**
- `OPENAI_API_KEY`
- `SLACK_BOT_TOKEN`
- `SLACK_CHANNEL_ID`
- `CLICKUP_API_KEY`

**Choose one configuration method:**
- `CLICKUP_LIST_ID` (single list)
- `CLICKUP_TEAM_ID` + upload `clickup_config.json` (multi-list)

### 3. Setup Cron Job

1. In Railway, add the **Cron** plugin to your project
2. Configure the cron job:
   - **Schedule**: `0 9 * * *` (runs daily at 9 AM UTC)
   - **Command**: `python main.py`
3. Deploy your changes

### 4. Monitor

Check Railway logs to ensure your bot is running correctly. The first run will happen at the next scheduled time.

## 🎭 Message Examples

The bot generates different types of messages based on task status:

- **Completed**: "🎉 @john just crushed the 'Update website copy' task! Someone's on fire today!"
- **Due Today**: "⏰ Hey @sarah, 'Design new mockups' is due today. Time to work some design magic!"
- **Overdue**: "🚨 @mike, 'Fix login bug' is overdue. Even bugs need closure!"
- **Unassigned**: "🤷 Who's brave enough to tackle 'Refactor authentication'? Any volunteers?"
- **No Due Date**: "📅 'Clean up database' has no due date. I guess it's due sometime before 2045! 🚀"

## 🔧 Customization

### Modify Message Prompts

Edit the prompts in `gpt_generator.py` to change the tone and style of messages:

```python
prompts = {
    "completed": f"Write a celebratory message for @{user} completing '{task}'...",
    # ... customize other prompts
}
```

### Change Schedule

Modify the cron schedule in Railway:
- `0 9 * * *` - Daily at 9 AM UTC
- `0 9 * * 1-5` - Weekdays only at 9 AM UTC
- `0 9,17 * * *` - Twice daily at 9 AM and 5 PM UTC

### Add More Task Statuses

Extend the logic in `clickup_fetcher.py` to handle additional task statuses or conditions.

## 📊 Logging & Monitoring

The bot includes comprehensive logging to help you monitor its operation and troubleshoot issues:

### Log Levels
- **INFO**: General operational information (task counts, status updates)
- **DEBUG**: Detailed execution information (API responses, task processing details)
- **WARNING**: Non-critical issues (invalid dates, empty responses)
- **ERROR**: Critical errors that prevent operation

### Log Outputs
- **Console**: Real-time logging output
- **File**: `clickup_bot.log` in the project directory

### Sample Log Output
```
2024-01-15 09:00:01 - __main__ - INFO - 🚀 Starting ClickUp Reminder Bot
2024-01-15 09:00:01 - clickup_fetcher - INFO - 🔍 Starting task fetch from ClickUp
2024-01-15 09:00:02 - clickup_fetcher - INFO - 📥 Retrieved 15 raw tasks from ClickUp
2024-01-15 09:00:02 - clickup_fetcher - INFO - 📊 Task categorization complete:
2024-01-15 09:00:02 - clickup_fetcher - INFO -    ✅ Completed: 3
2024-01-15 09:00:02 - clickup_fetcher - INFO -    📅 Due Today: 2
2024-01-15 09:00:02 - clickup_fetcher - INFO -    🚨 Overdue: 1
2024-01-15 09:00:03 - gpt_generator - INFO - 🤖 Generating message for task: 'Fix login bug'
2024-01-15 09:00:05 - gpt_generator - INFO - ✅ Successfully generated message via OpenAI
2024-01-15 09:00:05 - slack_sender - INFO - 💬 Preparing to send message to Slack
2024-01-15 09:00:06 - slack_sender - INFO - ✅ Message sent successfully to Slack
```

### Enable Debug Logging

For more detailed logs, modify the logging level in `main.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('clickup_bot.log')
    ]
)
```

## 🐛 Troubleshooting

### Common Issues

1. **"Missing environment variable"**: Ensure all required env vars are set
2. **OpenAI API errors**: Check your API key and billing status  
3. **Slack permission errors**: Verify bot permissions and channel access
4. **ClickUp API errors**: Confirm API key and list ID are correct

### Error Analysis

The logs will help you identify specific issues:

- **ClickUp API 401**: Invalid API key
- **ClickUp API 404**: Invalid List ID  
- **Slack "channel_not_found"**: Wrong channel ID
- **Slack "not_in_channel"**: Bot needs to be invited to channel
- **OpenAI errors**: API key or billing issues (bot will use fallback messages)

## 📄 License

MIT License - feel free to modify and use for your team!

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

**Happy task managing! 🎉**

## 🤖 User Mapping System

If your team's ClickUp usernames are different from Slack usernames, the bot can map them properly:

### Configuration

Create a `user_mapping.json` file:

```json
{
  "user_mappings": {
    "john.doe": "jdoe",
    "sarah.smith": "sarah",
    "mike.wilson": "mike.w"
  },
  "default_mention": "@channel",
  "fallback_behavior": "use_clickup_name"
}
```

### Management

Use the built-in user mapping manager:

```bash
# Interactive mode
python manage_users.py

# Command line options
python manage_users.py --show          # Show current mappings
python manage_users.py --add           # Add new mapping
python manage_users.py --test          # Test a mapping
python manage_users.py --import        # Bulk import mappings
```

### Fallback Behaviors

- `use_clickup_name`: Use @clickup_username if no mapping exists
- `use_default`: Use default mention (@channel) if no mapping exists

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

**Happy task managing! 🎉** 