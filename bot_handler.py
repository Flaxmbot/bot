from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
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
        if self.application:
            self._setup_handlers()

    def _setup_handlers(self):
        """Setup command and message handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self._start_command))
        self.application.add_handler(CommandHandler("help", self._help_command))
        self.application.add_handler(CommandHandler("devices", self._devices_command))
        self.application.add_handler(CommandHandler("users", self._users_command))
        self.application.add_handler(CommandHandler("adduser", self._add_user_command))
        self.application.add_handler(CommandHandler("removeuser", self._remove_user_command))
        self.application.add_handler(CommandHandler("list", self._list_command))
        self.application.add_handler(CommandHandler("download", self._download_command))
        self.application.add_handler(CommandHandler("delete", self._delete_command))
        self.application.add_handler(CommandHandler("search", self._search_command))
        self.application.add_handler(CommandHandler("status", self._status_command))
        
        # Message handler for non-command messages
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text_message))
        
        # Add a simple echo command for testing
        self.application.add_handler(CommandHandler("echo", self._echo_command))

    async def initialize(self):
        """Initialize the bot application"""
        if self.application:
            await self.application.initialize()

    async def process_update(self, update_data):
        """Process incoming update from Telegram"""
        try:
            logger.info(f"Processing update data: {update_data}")
            if self.application:
                # Let the telegram library handle the update properly
                update = Update.de_json(update_data, self.application.bot)
                logger.info(f"Converted to Update object: {update}")
                await self.application.process_update(update)
                logger.info("Update processed successfully")
        except Exception as e:
            logger.error(f"Error processing update: {e}")
            logger.exception(e)

    async def _check_authorization(self, update: Update) -> bool:
        """Check if user is authorized"""
        user_id = str(update.effective_user.id)
        logger.info(f"Checking authorization for user {user_id}")
        is_authorized = self.user_manager.is_authorized(user_id)
        logger.info(f"User {user_id} authorized: {is_authorized}")
        if not is_authorized:
            await update.message.reply_text("You are not authorized to use this bot. Please contact the administrator.")
            return False
        return True

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        logger.info(f"Received /start command from user {update.effective_user.id}")
        if not await self._check_authorization(update):
            logger.info(f"User {update.effective_user.id} not authorized for /start command")
            return
            
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
        await update.message.reply_text(message)

    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        logger.info(f"Received /help command from user {update.effective_user.id}")
        if not await self._check_authorization(update):
            logger.info(f"User {update.effective_user.id} not authorized for /help command")
            return
        await self._start_command(update, context)

    async def _devices_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /devices command"""
        if not await self._check_authorization(update):
            return
            
        user_id = str(update.effective_user.id)
        if not self.user_manager.is_admin(user_id):
            await update.message.reply_text("Only admin can list devices.")
            return
        
        devices = self.device_manager.get_all_devices()
        if not devices:
            await update.message.reply_text("No devices registered.")
            return
            
        message = "Registered devices:\n"
        for device_id, device_info in devices.items():
            status = "🟢 Online" if device_info.get('online_status', False) else "🔴 Offline"
            last_seen = device_info.get('last_seen', 'Never')
            message += f"\n{device_id} ({device_info.get('device_name', 'Unnamed')}) - {status} - Last seen: {last_seen}"
        
        await update.message.reply_text(message)

    async def _users_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /users command"""
        if not await self._check_authorization(update):
            return
            
        user_id = str(update.effective_user.id)
        if not self.user_manager.is_admin(user_id):
            await update.message.reply_text("Only admin can list users.")
            return
        
        users = self.user_manager.get_all_users()
        if not users:
            await update.message.reply_text("No users registered.")
            return
            
        message = "Authorized users:\n"
        for user_id, user_info in users.items():
            role = user_info.get('role', 'user')
            last_active = user_info.get('last_active', 'Never')
            message += f"\n{user_id} - {role} - Last active: {last_active}"
        
        await update.message.reply_text(message)

    async def _add_user_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /adduser command"""
        if not await self._check_authorization(update):
            return
            
        user_id = str(update.effective_user.id)
        if not self.user_manager.is_admin(user_id):
            await update.message.reply_text("Only admin can add users.")
            return
        
        args = context.args
        if not args:
            await update.message.reply_text("Please provide a user ID to add.\nUsage: /adduser <user_id>")
            return
        
        new_user_id = args[0]
        if self.user_manager.add_user(new_user_id, 'user'):
            await update.message.reply_text(f"User {new_user_id} added successfully.")
        else:
            await update.message.reply_text(f"Failed to add user {new_user_id}.")

    async def _remove_user_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /removeuser command"""
        if not await self._check_authorization(update):
            return
            
        user_id = str(update.effective_user.id)
        if not self.user_manager.is_admin(user_id):
            await update.message.reply_text("Only admin can remove users.")
            return
        
        args = context.args
        if not args:
            await update.message.reply_text("Please provide a user ID to remove.\nUsage: /removeuser <user_id>")
            return
        
        remove_user_id = args[0]
        if self.user_manager.remove_user(remove_user_id):
            await update.message.reply_text(f"User {remove_user_id} removed successfully.")
        else:
            await update.message.reply_text(f"Failed to remove user {remove_user_id}.")

    async def _list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /list command"""
        if not await self._check_authorization(update):
            return
            
        args = context.args
        path = args[0] if args else "."
        try:
            files = self.file_operations.list_directory(path)
            if not files:
                await update.message.reply_text(f"No files found in {path}")
                return
                
            message = f"Files in {path}:\n"
            for file in files[:50]:  # Limit to 50 files to avoid message size limits
                message += f"\n{file}"
            
            if len(files) > 50:
                message += f"\n... and {len(files) - 50} more files"
                
            await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error listing directory {path}: {e}")
            await update.message.reply_text(f"Error listing directory: {str(e)}")

    async def _download_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /download command"""
        if not await self._check_authorization(update):
            return
            
        args = context.args
        if not args:
            await update.message.reply_text("Please provide a file path.\nUsage: /download <file_path>")
            return
            
        file_path = args[0]
        try:
            if self.file_operations.file_exists(file_path):
                # For now, we'll send a placeholder message
                # In a real implementation, we would send the actual file
                await update.message.reply_text(f"File download would start for: {file_path}")
                # await update.message.reply_document(document=open(file_path, 'rb'))
            else:
                await update.message.reply_text(f"File not found: {file_path}")
        except Exception as e:
            logger.error(f"Error downloading file {file_path}: {e}")
            await update.message.reply_text(f"Error downloading file: {str(e)}")

    async def _delete_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /delete command"""
        if not await self._check_authorization(update):
            return
            
        args = context.args
        if not args:
            await update.message.reply_text("Please provide a file path.\nUsage: /delete <file_path>")
            return
            
        file_path = args[0]
        try:
            if self.file_operations.file_exists(file_path):
                self.file_operations.delete_file(file_path)
                await update.message.reply_text(f"File deleted: {file_path}")
            else:
                await update.message.reply_text(f"File not found: {file_path}")
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            await update.message.reply_text(f"Error deleting file: {str(e)}")

    async def _search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /search command"""
        if not await self._check_authorization(update):
            return
            
        args = context.args
        if not args:
            await update.message.reply_text("Please provide a search query.\nUsage: /search <query>")
            return
            
        query = ' '.join(args)
        try:
            results = self.file_operations.search_files(query)
            if not results:
                await update.message.reply_text(f"No files found matching: {query}")
                return
                
            message = f"Search results for '{query}':\n"
            for file in results[:20]:  # Limit to 20 files
                message += f"\n{file}"
            
            if len(results) > 20:
                message += f"\n... and {len(results) - 20} more files"
                
            await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error searching for {query}: {e}")
            await update.message.reply_text(f"Error searching files: {str(e)}")

    async def _status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        if not await self._check_authorization(update):
            return
        await update.message.reply_text("Bot is running and operational.")

    async def _handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        if not await self._check_authorization(update):
            return
        await update.message.reply_text("I only respond to commands. Type /help for available commands.")
    async def _echo_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /echo command for testing"""
        logger.info(f"Received /echo command from user {update.effective_user.id}")
        if not await self._check_authorization(update):
            logger.info(f"User {update.effective_user.id} not authorized for /echo command")
            return
            
        args = context.args
        if not args:
            await update.message.reply_text("Please provide text to echo.\nUsage: /echo <text>")
            return
            
        text = ' '.join(args)
        logger.info(f"Echoing text: {text}")
        await update.message.reply_text(f"Echo: {text}")