from flask import Flask, request, jsonify
import os
import json
import logging
import asyncio
import requests
from bot_handler import BotCommandHandler
from device_manager import DeviceManager
from user_management import UserManager
from file_operations import FileOperations
from config import Config
from utils import setup_logging
def get_webhook_info(bot_token):
    """Get current webhook information"""
    try:
        import requests
        url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
        response = requests.get(url)
        return response.json()
    except Exception as e:
        logger.error(f"Error getting webhook info: {e}")
        return None

def set_webhook_url(bot_token, webhook_url):
    """Set the webhook URL for the bot"""
    try:
        import requests
        url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
        data = {'url': webhook_url}
        response = requests.post(url, data=data)
        logger.info(f"Set webhook response: {response.json()}")
        return response.json()
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return None

def check_and_set_webhook(bot_token, expected_url):
    """Check current webhook and set it if not correct"""
    try:
        # Get current webhook info
        webhook_info = get_webhook_info(bot_token)
        if not webhook_info or not webhook_info.get('ok'):
            logger.error(f"Failed to get webhook info: {webhook_info}")
            return False
            
        current_url = webhook_info.get('result', {}).get('url')
        logger.info(f"Current webhook URL: {current_url}")
        logger.info(f"Expected webhook URL: {expected_url}")
        
        # Check if webhook is already set correctly
        if current_url == expected_url:
            logger.info("Webhook is already set correctly")
            return True
            
        # Set webhook if not correct
        logger.info("Setting webhook to correct URL")
        result = set_webhook_url(bot_token, expected_url)
        return result and result.get('ok', False)
    except Exception as e:
        logger.error(f"Error checking and setting webhook: {e}")
        return False

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Load configuration
config = Config()

# Validate configuration
config_errors = config.validate()
if config_errors:
    logger.error("Configuration errors: %s", config_errors)
    # In a production environment, you might want to exit here

# Initialize managers
user_manager = UserManager(config.STORAGE_PATH)
device_manager = DeviceManager(config.STORAGE_PATH)
file_operations = FileOperations()
logger.info("Initializing BotCommandHandler")
bot_handler = BotCommandHandler(config.BOT_TOKEN, config.ADMIN_ID, user_manager, device_manager, file_operations)
logger.info(f"BotCommandHandler initialized with application: {bool(bot_handler.application)}")

# Initialize the bot application
async def initialize_bot():
    logger.info("Initializing bot")
    if bot_handler.application:
        await bot_handler.initialize()
        logger.info("Bot initialized successfully")
    else:
        logger.error("Cannot initialize bot - application is None")

# Create event loop for async operations
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
logger.info("Running bot initialization")
loop.run_until_complete(initialize_bot())
logger.info("Bot initialization completed")

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook requests from Telegram"""
    logger.info("Webhook endpoint called")
    try:
        # Log raw request data
        logger.info(f"Request headers: {dict(request.headers)}")
        logger.info(f"Request data: {request.get_data()}")
        
        update = request.get_json()
        logger.info(f"Received update: {update}")
        
        # Check if update is None
        if update is None:
            logger.error("Failed to parse JSON from request")
            return jsonify({'status': 'error', 'message': 'Invalid JSON'}), 400
        
        # Process the update
        # Use asyncio.run() which creates a new event loop each time
        # This is safer in a multi-threaded environment like Flask
        logger.info("Processing update with bot handler")
        asyncio.run(bot_handler.process_update(update))
        logger.info("Update processed successfully")
        
        return jsonify({'status': 'ok'})
    except asyncio.TimeoutError:
        logger.error("Timeout processing update")
        return jsonify({'status': 'error', 'message': 'Processing timeout'}), 500
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        logger.exception(e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/webhook_info', methods=['GET'])
def webhook_info():
    """Get current webhook information from Telegram"""
    try:
        if not config.BOT_TOKEN:
            return jsonify({'error': 'BOT_TOKEN not configured'}), 400
            
        url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/getWebhookInfo"
        response = requests.get(url)
        return jsonify(response.json())
    except Exception as e:
        logger.error(f"Error getting webhook info: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/set_webhook', methods=['POST'])
def set_webhook():
    """Set webhook for the bot"""
    try:
        if not config.BOT_TOKEN:
            return jsonify({'error': 'BOT_TOKEN not configured'}), 400
            
        # Get the base URL from the request or use RENDER_EXTERNAL_URL or request host
        base_url = request.args.get('url') or os.environ.get('RENDER_EXTERNAL_URL') or request.host_url.rstrip('/')
        webhook_url = f"{base_url}/webhook"
        
        url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/setWebhook"
        data = {'url': webhook_url}
        response = requests.post(url, data=data)
        
        logger.info(f"Set webhook to: {webhook_url}")
        return jsonify(response.json())
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/check_and_set_webhook', methods=['POST'])
def check_and_set_webhook_endpoint():
    """Check current webhook and set it if not correct"""
    try:
        if not config.BOT_TOKEN:
            return jsonify({'error': 'BOT_TOKEN not configured'}), 400
            
        # Get the base URL from the request or use RENDER_EXTERNAL_URL or request host
        base_url = request.args.get('url') or os.environ.get('RENDER_EXTERNAL_URL') or request.host_url.rstrip('/')
        webhook_url = f"{base_url}/webhook"
        
        success = check_and_set_webhook(config.BOT_TOKEN, webhook_url)
        
        if success:
            return jsonify({'status': 'success', 'message': 'Webhook checked and set correctly'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to check or set webhook'}), 500
    except Exception as e:
        logger.error(f"Error checking and setting webhook: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'bot_token_set': bool(config.BOT_TOKEN)})

@app.route('/devices', methods=['GET'])
def get_devices():
    """Get all registered devices (admin only)"""
    # In a real implementation, this would check authentication
    devices = device_manager.get_all_devices()
    return jsonify(devices)

@app.route('/test', methods=['GET'])
def test():
    """Simple test endpoint"""
    logger.info("Test endpoint called")
    return jsonify({'status': 'ok', 'message': 'Test endpoint working'})

@app.route('/register', methods=['POST'])
def register_device():
    """Register a new device"""
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        device_name = data.get('device_name', 'Unknown Device')
        
        if not device_id:
            return jsonify({'error': 'device_id is required'}), 400
            
        # Register device
        device_manager.register_device(device_id, device_name)
        
        # Notify admin about new device registration
        if config.ADMIN_ID and bot_handler.application:
            try:
                message = f"📱 New device registered!\n\nID: {device_id}\nDevice: {device_name}\nTime: {data.get('registration_date', 'Unknown')}\n\n#newdevice #registration"
                # Use asyncio.run() for proper async handling in Flask context
                asyncio.run(bot_handler.application.bot.send_message(
                    chat_id=config.ADMIN_ID,
                    text=message
                ))
            except Exception as e:
                logger.error(f"Failed to notify admin about new device: {e}")
        
        return jsonify({'status': 'success', 'message': 'Device registered successfully'})
    except Exception as e:
        logger.error(f"Error registering device: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/heartbeat', methods=['POST'])
def device_heartbeat():
    """Update device status"""
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        
        if not device_id:
            return jsonify({'error': 'device_id is required'}), 400
            
        # Update device status
        device_manager.update_device_status(device_id, data.get('online_status', True))
        
        return jsonify({'status': 'success', 'message': 'Heartbeat received'})
    except Exception as e:
        logger.error(f"Error processing heartbeat: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/command', methods=['POST'])
def handle_command():
    """Handle commands from the Flutter app"""
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        command = data.get('command')
        params = data.get('params', {})
        
        if not device_id or not command:
            return jsonify({'error': 'device_id and command are required'}), 400
            
        # Verify device is registered
        device = device_manager.get_device(device_id)
        if not device:
            return jsonify({'error': 'Device not registered'}), 403
            
        # Process command
        result = None
        success = False
        message = ""
        
        if command == 'list':
            path = params.get('path', '.')
            try:
                files = file_operations.list_directory(path)
                result = {'files': files}
                success = True
            except Exception as e:
                message = f"Error listing directory: {str(e)}"
        elif command == 'search':
            query = params.get('query', '')
            try:
                files = file_operations.search_files(query)
                result = {'files': files}
                success = True
            except Exception as e:
                message = f"Error searching files: {str(e)}"
        elif command == 'status':
            try:
                result = {
                    'status': 'online',
                    'device_id': device_id,
                    'device_name': device.get('device_name', 'Unknown'),
                    'last_seen': device.get('last_seen', 'Unknown')
                }
                success = True
            except Exception as e:
                message = f"Error getting status: {str(e)}"
        elif command == 'devices':
            # Only allow admin users to list devices
            if not user_manager.is_admin(str(request.headers.get('X-User-ID', ''))):
                return jsonify({'error': 'Unauthorized'}), 403
            try:
                devices = device_manager.get_all_devices()
                result = {'devices': devices}
                success = True
            except Exception as e:
                message = f"Error getting devices: {str(e)}"
        elif command == 'users':
            # Only allow admin users to list users
            if not user_manager.is_admin(str(request.headers.get('X-User-ID', ''))):
                return jsonify({'error': 'Unauthorized'}), 403
            try:
                users = user_manager.get_all_users()
                result = {'users': users}
                success = True
            except Exception as e:
                message = f"Error getting users: {str(e)}"
        else:
            message = f"Unknown command: {command}"
        
        response = {
            'success': success,
            'message': message,
            'result': result
        }
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error handling command: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create storage directory if it doesn't exist
    os.makedirs(config.STORAGE_PATH, exist_ok=True)
    
    # Initialize with admin user
    user_manager.add_user(config.ADMIN_ID, 'admin')
    
    # Check and set webhook
    if config.BOT_TOKEN:
        # Try to get the external URL from environment variable
        external_url = os.environ.get('RENDER_EXTERNAL_URL')
        if external_url:
            webhook_url = f"{external_url}/webhook"
            logger.info(f"Checking and setting webhook to: {webhook_url}")
            check_and_set_webhook(config.BOT_TOKEN, webhook_url)
        else:
            logger.info("RENDER_EXTERNAL_URL not set, skipping automatic webhook setup")
    
    # Send startup message to admin
    async def send_startup_message():
        if bot_handler.application and config.ADMIN_ID:
            try:
                await bot_handler.application.bot.send_message(
                    chat_id=config.ADMIN_ID,
                    text='Bot is now online and operational!'
                )
            except Exception as e:
                logger.error(f"Failed to send startup message: {e}")
    
    # Run the startup message in the event loop
    if bot_handler.application:
        loop.run_until_complete(send_startup_message())
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=config.PORT)