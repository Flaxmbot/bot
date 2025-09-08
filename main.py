from flask import Flask, request, jsonify
import os
import json
import logging
from bot_handler import BotCommandHandler
from device_manager import DeviceManager
from user_management import UserManager
from file_operations import FileOperations
from config import Config
from utils import setup_logging

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
bot_handler = BotCommandHandler(config.BOT_TOKEN, config.ADMIN_ID, user_manager, device_manager, file_operations)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook requests from Telegram"""
    try:
        update = request.get_json()
        logger.info(f"Received update: {update}")
        
        # Process the update
        bot_handler.process_update(update)
        
        return jsonify({'status': 'ok'})
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

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

if __name__ == '__main__':
    # Create storage directory if it doesn't exist
    os.makedirs(config.STORAGE_PATH, exist_ok=True)
    
    # Initialize with admin user
    user_manager.add_user(config.ADMIN_ID, 'admin')
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=config.PORT)