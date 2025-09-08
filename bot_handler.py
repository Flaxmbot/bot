from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import logging
import os
import json

logger = logging.getLogger(__name__)

class BotCommandHandler:
    def __init__(self, bot_token, admin_id, user_manager, device_manager, file_operations):
        self.bot_token = bot_token
        self.admin_id = admin_id
        self.user_manager = user_manager
        self.device_manager = device_manager
        self.file_operations = file_operations
        self.application = Application.builder().token(bot_token).build() if bot_token else None

    async def process_update(self, update_data):
        """Process incoming update from Telegram"""
        try:
            # Convert dict to Update object
            update = Update.de_json(update_data)
            
            if update.message:
                await self.handle_message(update.message)
            # Note: callback queries are not implemented in this version
        except Exception as e:
            logger.error(f"Error processing update: {e})

    async def handle_message(self, message):
        """Handle incoming messages"""
        user_id = str(message.from_user.id)
        chat_id = message.chat.id
        text = message.text
        
        logger.info(f"Received message from {user_id}: {text}")
        
        # Check if user is authorized
        if not self.user_manager.is_authorized(user_id):
            await self.application.bot.send_message(chat_id=chat_id, text="You are not authorized to use this bot. Please contact the administrator.")
            return
        
        # Parse command
        if text.startswith('/'):
            await self.handle_command(message, user_id, chat_id, text)
        else:
            await self.handle_text_message(message, user_id, chat_id, text)

    async def handle_command(self, message, user_id, chat_id, text):
        """Handle command messages"""
        parts = text.split(' ')
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        try:
            if command == '/start':
                await self.start_command(chat_id)
            elif command == '/help':
                await self.help_command(chat_id)
            elif command == '/devices':
                await self.devices_command(user_id, chat_id)
            elif command == '/users':
                await self.users_command(user_id, chat_id)
            elif command == '/adduser':
                await self.add_user_command(user_id, chat_id, args)
            elif command == '/removeuser':
                await self.remove_user_command(user_id, chat_id, args)
            elif command == '/list':
                await self.list_command(user_id, chat_id, args)
            elif command == '/download':
                await self.download_command(user_id, chat_id, args)
            elif command == '/delete':
                await self.delete_command(user_id, chat_id, args)
            elif command == '/search':
                await self.search_command(user_id, chat_id, args)
            elif command == '/status':
                await self.status_command(user_id, chat_id)
            else:
                await self.application.bot.send_message(chat_id=chat_id, text="Unknown command. Type /help for available commands.")
        except Exception as e:
            logger.error(f"Error handling command {command}: {e}")
            await self.application.bot.send_message(chat_id=chat_id, text="An error occurred while processing your command.")

    async def handle_text_message(self, message, user_id, chat_id, text):
        """Handle text messages"""
        await self.application.bot.send_message(chat_id=chat_id, text="I only respond to commands. Type /help for available commands.")

    async def start_command(self, chat_id):
        """Handle /start command"""
        message = """
Welcome to Flutter File Manager Bot!

Available commands:
/list <path> - List directory contents
/download <file_path> - Download a file
/delete <file_path> - Delete a file
/search <query> - Search for files
/status - Show device status
/help - Show this help message

Admin commands:
/devices - List all registered devices
/adduser <user_id> - Add authorized user
/removeuser <user_id> - Remove authorized user
/users - List all authorized users
"""
        await self.application.bot.send_message(chat_id=chat_id, text=message)

    async def help_command(self, chat_id):
        """Handle /help command"""
        await self.start_command(chat_id)

    async def devices_command(self, user_id, chat_id):
        """Handle /devices command"""
        if not self.user_manager.is_admin(user_id):
            await self.application.bot.send_message(chat_id=chat_id, text="Only admin can list devices.")
            return
        
        devices = self.device_manager.get_all_devices()
        if not devices:
            await self.application.bot.send_message(chat_id=chat_id, text="No devices registered.")
            return
            
        message = "Registered devices:\n"
        for device_id, device_info in devices.items():
            status = "🟢 Online" if device_info.get('online_status', False) else "🔴 Offline"
            last_seen = device_info.get('last_seen', 'Never')
            message += f"\n{device_id} ({device_info.get('device_name', 'Unnamed')}) - {status} - Last seen: {last_seen}"
        
        await self.application.bot.send_message(chat_id=chat_id, text=message)

    async def users_command(self, user_id, chat_id):
        """Handle /users command"""
        if not self.user_manager.is_admin(user_id):
            await self.application.bot.send_message(chat_id=chat_id, text="Only admin can list users.")
            return
        
        users = self.user_manager.get_all_users()
        if not users:
            await self.application.bot.send_message(chat_id=chat_id, text="No users registered.")
            return
            
        message = "Authorized users:\n"
        for user_id, user_info in users.items():
            role = user_info.get('role', 'user')
            last_active = user_info.get('last_active', 'Never')
            message += f"\n{user_id} - {role} - Last active: {last_active}"
        
        await self.application.bot.send_message(chat_id=chat_id, text=message)

    async def add_user_command(self, user_id, chat_id, args):
        """Handle /adduser command"""
        if not self.user_manager.is_admin(user_id):
            await self.application.bot.send_message(chat_id=chat_id, text="Only admin can add users.")
            return
        
        if not args:
            await self.application.bot.send_message(chat_id=chat_id, text="Please provide a user ID to add.\nUsage: /adduser <user_id>")
            return
        
        new_user_id = args[0]
        if self.user_manager.add_user(new_user_id, 'user'):
            await self.application.bot.send_message(chat_id=chat_id, text=f"User {new_user_id} added successfully.")
        else:
            await self.application.bot.send_message(chat_id=chat_id, text=f"Failed to add user {new_user_id}.")

    async def remove_user_command(self, user_id, chat_id, args):
        """Handle /removeuser command"""
        if not self.user_manager.is_admin(user_id):
            await self.application.bot.send_message(chat_id=chat_id, text="Only admin can remove users.")
            return
        
        if not args:
            await self.application.bot.send_message(chat_id=chat_id, text="Please provide a user ID to remove.\nUsage: /removeuser <user_id>")
            return
        
        remove_user_id = args[0]
        if self.user_manager.remove_user(remove_user_id):
            await self.application.bot.send_message(chat_id=chat_id, text=f"User {remove_user_id} removed successfully.")
        else:
            await self.application.bot.send_message(chat_id=chat_id, text=f"Failed to remove user {remove_user_id}.")

    async def list_command(self, user_id, chat_id, args):
        """Handle /list command"""
        path = args[0] if args else "."
        try:
            files = self.file_operations.list_directory(path)
            if not files:
                await self.application.bot.send_message(chat_id=chat_id, text=f"No files found in {path}")
                return
                
            message = f"Files in {path}:\n"
            for file in files[:50]:  # Limit to 50 files to avoid message size limits
                message += f"\n{file}"
            
            if len(files) > 50:
                message += f"\n... and {len(files) - 50} more files"
                
            await self.application.bot.send_message(chat_id=chat_id, text=message)
        except Exception as e:
            logger.error(f"Error listing directory {path}: {e}")
            await self.application.bot.send_message(chat_id=chat_id, text=f"Error listing directory: {str(e)}")

    async def download_command(self, user_id, chat_id, args):
        """Handle /download command"""
        if not args:
            await self.application.bot.send_message(chat_id=chat_id, text="Please provide a file path.\nUsage: /download <file_path>")
            return
            
        file_path = args[0]
        try:
            if self.file_operations.file_exists(file_path):
                # For now, we'll send a placeholder message
                # In a real implementation, we would send the actual file
                await self.application.bot.send_message(chat_id=chat_id, text=f"File download would start for: {file_path}")
                # await self.application.bot.send_document(chat_id=chat_id, document=open(file_path, 'rb'))
            else:
                await self.application.bot.send_message(chat_id=chat_id, text=f"File not found: {file_path}")
        except Exception as e:
            logger.error(f"Error downloading file {file_path}: {e}")
            await self.application.bot.send_message(chat_id=chat_id, text=f"Error downloading file: {str(e)}")

    async def delete_command(self, user_id, chat_id, args):
        """Handle /delete command"""
        if not args:
            await self.application.bot.send_message(chat_id=chat_id, text="Please provide a file path.\nUsage: /delete <file_path>")
            return
            
        file_path = args[0]
        try:
            if self.file_operations.file_exists(file_path):
                self.file_operations.delete_file(file_path)
                await self.application.bot.send_message(chat_id=chat_id, text=f"File deleted: {file_path}")
            else:
                await self.application.bot.send_message(chat_id=chat_id, text=f"File not found: {file_path}")
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            await self.application.bot.send_message(chat_id=chat_id, text=f"Error deleting file: {str(e)}")

    async def search_command(self, user_id, chat_id, args):
        """Handle /search command"""
        if not args:
            await self.application.bot.send_message(chat_id=chat_id, text="Please provide a search query.\nUsage: /search <query>")
            return
            
        query = ' '.join(args)
        try:
            results = self.file_operations.search_files(query)
            if not results:
                await self.application.bot.send_message(chat_id=chat_id, text=f"No files found matching: {query}")
                return
                
            message = f"Search results for '{query}':\n"
            for file in results[:20]:  # Limit to 20 files
                message += f"\n{file}"
            
            if len(results) > 20:
                message += f"\n... and {len(results) - 20} more files"
                
            await self.application.bot.send_message(chat_id=chat_id, text=message)
        except Exception as e:
            logger.error(f"Error searching for {query}: {e}")
            await self.application.bot.send_message(chat_id=chat_id, text=f"Error searching files: {str(e)}")

    async def status_command(self, user_id, chat_id):
        """Handle /status command"""
        await self.application.bot.send_message(chat_id=chat_id, text="Bot is running and operational.")