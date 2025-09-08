# Deployment Guide for Render Platform

This guide explains how to deploy the Telegram bot server on the Render platform.

## Prerequisites

1. Create an account on [Render](https://render.com)
2. Create a new Telegram bot using BotFather on Telegram
3. Note down the bot token provided by BotFather

## Deployment Steps

### 1. Prepare Your Repository

1. Make sure all the bot files are in your Git repository:
   - `main.py` (entry point)
   - `bot_handler.py` (Telegram bot logic)
   - `user_management.py` (User authentication and management)
   - `device_manager.py` (Device registration and management)
   - `file_operations.py` (File management functions)
   - `config.py` (Configuration management)
   - `utils.py` (Utility functions)
   - `requirements.txt` (Dependencies)
   - `runtime.txt` (Python version specification)

### 2. Create a New Web Service on Render

1. Log in to your Render account
2. Click "New" and select "Web Service"
3. Connect your Git repository containing the bot files
4. Configure the following settings:
   - Name: Give your service a name (e.g., `flutter-file-manager-bot`)
   - Region: Choose the region closest to your users
   - Branch: Select the branch to deploy (usually `main` or `master`)
   - Root Directory: Leave empty if files are in the root, or specify the path
   - Environment: Select "Python 3"
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main.py`

### 3. Configure Environment Variables

In the "Environment Variables" section, add the following variables:
- `BOT_TOKEN`: Your Telegram bot token from BotFather
- `ADMIN_ID`: Your Telegram user ID (5445671392 by default)
- `STORAGE_PATH`: Path for temporary file storage (e.g., `/tmp/bot_storage`)

### 4. Advanced Settings

1. In the "Advanced" section, you can:
   - Set auto-deploy to true if you want automatic deployments on git pushes
   - Add health check settings
   - Configure custom domains if needed

### 5. Deploy the Service

1. Click "Create Web Service"
2. Render will automatically start building and deploying your service
3. Wait for the deployment to complete (this may take a few minutes)

### 6. Configure the Telegram Webhook

After deployment is complete:

1. Get your service URL from Render (usually in the format: `https://your-service-name.onrender.com`)
2. Your webhook endpoint will be: `https://your-service-name.onrender.com/webhook`
3. Set the webhook using the Telegram Bot API:
   ```
   https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=https://your-service-name.onrender.com/webhook
   ```

## Render-Specific Configuration

### Python Version

The `runtime.txt` file specifies Python 3.11, which is compatible with the latest python-telegram-bot library.

### Automatic Restart

Render automatically restarts your service if it crashes, ensuring high availability.

### Scaling

Render's free tier includes:
- 512 MB RAM
- 100 GB bandwidth
- 100 hours of runtime per month

For production use, consider upgrading to a paid plan for more resources.

## Monitoring and Logs

1. View logs in real-time from the Render dashboard
2. Set up notifications for deployment success/failure
3. Monitor resource usage (CPU, memory, disk)

## Troubleshooting

### Common Issues

1. **Service fails to start**
   - Check the logs for error messages
   - Verify all environment variables are set correctly
   - Ensure requirements.txt includes all necessary packages

2. **Bot not responding**
   - Check that the webhook is correctly set
   - Verify the BOT_TOKEN is correct
   - Check network connectivity

3. **File operations failing**
   - Verify the STORAGE_PATH exists and is writable
   - Check file permissions

### Debugging Tips

1. Use `print()` statements in your code to debug (visible in Render logs)
2. Check the "Logs" tab in the Render dashboard
3. Test your webhook URL with a tool like curl

## Updating Your Bot

To update your bot:

1. Make changes to your code
2. Commit and push to your Git repository
3. If auto-deploy is enabled, Render will automatically deploy the changes
4. If auto-deploy is disabled, manually trigger a deploy from the Render dashboard

## Cost Considerations

- The free tier is sufficient for development and light usage
- For production bots with heavy usage, consider upgrading to a paid plan
- Monitor your usage to avoid unexpected charges