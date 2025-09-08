# Telegram Bot Server for Flutter File Manager

This is the server-side component of the Telegram bot integration for the Flutter File Manager application. It provides remote file access capabilities through Telegram commands.

## Features

- File upload, download, and deletion
- Directory listing and file search
- User management (admin-only user addition/removal)
- Device registration and management
- Security controls and access logging

## Deployment to bots.business

### Prerequisites

1. Create an account on [bots.business](https://bots.business)
2. Create a new Telegram bot using BotFather on Telegram
3. Note down the bot token provided by BotFather

### Deployment Steps

1. Log in to your bots.business account
2. Create a new bot project
3. Upload all files from this directory to your bot project:
   - `main.py` (entry point)
   - `bot_handler.py` (Telegram bot logic)
   - `user_management.py` (User authentication and management)
   - `device_manager.py` (Device registration and management)
   - `file_operations.py` (File management functions)
   - `config.py` (Configuration management)
   - `utils.py` (Utility functions)
   - `requirements.txt` (Dependencies)

4. Configure environment variables in the bots.business dashboard:
   - `BOT_TOKEN`: Your Telegram bot token from BotFather
   - `ADMIN_ID`: Your Telegram user ID (5445671392 by default)
   - `STORAGE_PATH`: Path for temporary file storage (default: /tmp/bot_storage)

5. Set the main file to `main.py`

6. Deploy the bot

### Webhook Configuration

After deployment, you need to set up the webhook for your bot:

1. Get your bot's webhook URL from bots.business (usually in the format: `https://api.bots.business/webhooks/your-bot-id`)
2. Set the webhook using the Telegram Bot API:
   ```
   https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=<WEBHOOK_URL>
   ```

### Required Dependencies

The bot requires the following Python packages:
- python-telegram-bot==13.15
- flask==2.3.2
- requests==2.31.0

These are automatically installed by bots.business based on requirements.txt.

## Commands

### User Commands
- `/start` - Initialize bot and show help
- `/list <path>` - List directory contents
- `/download <file_path>` - Download file from device
- `/delete <file_path>` - Delete file from device
- `/search <query>` - Search for files
- `/status` - Show device status
- `/help` - Show help information

### Admin Commands
- `/devices` - List registered devices
- `/adduser <user_id>` - Add authorized user
- `/removeuser <user_id>` - Remove authorized user
- `/users` - List authorized users

## Security

- Only authorized users can interact with the bot
- Only admin can add/remove users
- File operations are restricted to prevent directory traversal
- All actions are logged for audit purposes
- Rate limiting prevents abuse

## Data Models

### Device Model
```json
{
  "device_id": "unique_device_identifier",
  "registration_date": "timestamp",
  "last_seen": "timestamp",
  "device_name": "string",
  "online_status": "boolean"
}
```

### User Model
```json
{
  "user_id": "telegram_user_id",
  "role": "admin|user",
  "registration_date": "timestamp",
  "last_active": "timestamp"
}
```

## Troubleshooting

### Bot Not Responding
- Check bots.business logs for errors
- Verify webhook URL is correctly configured
- Ensure BOT_TOKEN environment variable is set correctly
- Check network connectivity

### Device Not Registering
- Verify first-launch detection logic in the Flutter app
- Check network connectivity from device
- Ensure bot server is running and accessible
- Validate device ID generation

## Development

To run locally for development:

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set environment variables:
   ```
   export BOT_TOKEN="your_bot_token"
   export ADMIN_ID="your_telegram_id"
   export STORAGE_PATH="/tmp/bot_storage"
   ```

3. Run the server:
   ```
   python main.py
   ```

4. Use ngrok or similar to expose your local server to the internet for webhook testing