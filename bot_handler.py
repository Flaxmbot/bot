from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging
import os
import json
import asyncio

logger = logging.getLogger(__name__)

class BotCommandHandler:
    def __init__(self, bot_token, admin_id, user_manager, device_manager, file_operations):
        self.bot_token = bot_token
        self.admin_id = admin_id
        self.user_manager = user_manager
        self.device_manager = device_manager
        self.file_operations = file_operations
        logger.info(f"Initializing BotCommandHandler with bot_token: {bool(bot_token)}")
        self.application = Application.builder().token(bot_token).build() if bot_token else None
        logger.info(f"Application created: {bool(self.application)}")
        if self.application:
            self._setup_handlers()
            logger.info("Handlers set up successfully")
        else:
            logger.error("Failed to create application - bot_token may be invalid or missing")

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
        
        # Add menu command for easier navigation
        self.application.add_handler(CommandHandler("menu", self._menu_command))

    async def initialize(self):
        """Initialize the bot application"""
        logger.info("Initializing bot application")
        if self.application:
            await self.application.initialize()
            logger.info("Bot application initialized successfully")
        else:
            logger.error("Cannot initialize bot application - application is None")

    async def process_update(self, update_data):
        """Process incoming update from Telegram"""
        try:
            if self.application:
                # Let the telegram library handle the update properly
                update = Update.de_json(update_data, self.application.bot)
                if update:
                    await self.application.process_update(update)
                else:
                    logger.error("Failed to convert update data to Update object")
            else:
                logger.error("Application is None, cannot process update")
        except Exception as e:
            logger.error(f"Error processing update: {e}")

    async def _check_authorization(self, update: Update) -> bool:
        """Check if user is authorized"""
        user_id = str(update.effective_user.id)
        is_authorized = self.user_manager.is_authorized(user_id)
        if not is_authorized:
            await update.message.reply_text("You are not authorized to use this bot. Please contact the administrator.")
            return False
        return True

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        if not await self._check_authorization(update):
            return
            
        message = """
📱 *Flutter File Manager Bot* 📱

Welcome to your file management assistant!

Use /menu to access the interactive menu with all available commands.

*Tip:* Use the commands to manage your files remotely!
        """
        await update.message.reply_text(message, parse_mode='Markdown')

    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        if not await self._check_authorization(update):
            return
            
        user_id = str(update.effective_user.id)
        is_admin = self.user_manager.is_admin(user_id)
        
        message = "📱 *Flutter File Manager - Help*\n\n"
        message += "This bot allows you to manage files remotely.\n\n"
        
        message += "📁 *File Operations*\n"
        message += "• /list <path> - List directory contents (default: current directory)\n"
        message += "• /search <query> - Search for files by name\n"
        message += "• /download <file_path> - Download a file\n"
        message += "• /delete <file_path> - Delete a file\n\n"
        
        message += "📊 *Device Management*\n"
        message += "• /status - Show device status\n"
        
        if is_admin:
            message += "• /devices - List all registered devices\n\n"
            message += "👥 *User Management* (Admin only)\n"
            message += "• /users - List all authorized users\n"
            message += "• /adduser <user_id> - Add authorized user\n"
            message += "• /removeuser <user_id> - Remove authorized user\n\n"
        else:
            message += "\n"
            
        message += "ℹ️ *Other Commands*\n"
        message += "• /menu - Show interactive menu\n"
        message += "• /help - Show this help message\n"
        message += "• /status - Bot status\n\n"
        
        message += "*Tips:*\n"
        message += "• Use quotes around paths with spaces\n"
        message += "• File paths are relative to the bot's root directory\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')

    async def _devices_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /devices command"""
        if not await self._check_authorization(update):
            return
            
        user_id = str(update.effective_user.id)
        if not self.user_manager.is_admin(user_id):
            await update.message.reply_text("🔐 Only admin can list devices.")
            return
        
        devices = self.device_manager.get_all_devices()
        if not devices:
            await update.message.reply_text("📱 No devices registered.")
            return
            
        message = "📱 *Registered Devices*\n\n"
        for device_id, device_info in devices.items():
            status = "🟢 Online" if device_info.get('online_status', False) else "🔴 Offline"
            last_seen = device_info.get('last_seen', 'Never')
            registration_date = device_info.get('registration_date', 'Unknown')
            message += f"🔹 *{device_info.get('device_name', 'Unnamed')}*\n"
            message += f"   ID: `{device_id}`\n"
            message += f"   Status: {status}\n"
            message += f"   Last seen: {last_seen}\n"
            message += f"   Registered: {registration_date}\n\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')

    async def _users_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /users command"""
        if not await self._check_authorization(update):
            return
            
        user_id = str(update.effective_user.id)
        if not self.user_manager.is_admin(user_id):
            await update.message.reply_text("🔐 Only admin can list users.")
            return
        
        users = self.user_manager.get_all_users()
        if not users:
            await update.message.reply_text("👥 No users registered.")
            return
            
        message = "👥 *Authorized Users*\n\n"
        for user_id, user_info in users.items():
            role = user_info.get('role', 'user')
            last_active = user_info.get('last_active', 'Never')
            message += f"🔹 *User ID:* `{user_id}`\n"
            message += f"   Role: {role}\n"
            message += f"   Last active: {last_active}\n\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')

    async def _add_user_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /adduser command"""
        if not await self._check_authorization(update):
            return
            
        user_id = str(update.effective_user.id)
        if not self.user_manager.is_admin(user_id):
            await update.message.reply_text("🔐 Only admin can add users.")
            return
        
        args = context.args
        if not args:
            await update.message.reply_text("📝 Please provide a user ID to add.\n\n*Usage:* `/adduser <user_id>`", parse_mode='Markdown')
            return
        
        new_user_id = args[0]
        try:
            if self.user_manager.add_user(new_user_id, 'user'):
                await update.message.reply_text(f"✅ User `{new_user_id}` added successfully.", parse_mode='Markdown')
            else:
                await update.message.reply_text(f"❌ Failed to add user `{new_user_id}`.", parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error adding user {new_user_id}: {e}")
            await update.message.reply_text(f"❌ Error adding user: {str(e)}")

    async def _remove_user_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /removeuser command"""
        if not await self._check_authorization(update):
            return
            
        user_id = str(update.effective_user.id)
        if not self.user_manager.is_admin(user_id):
            await update.message.reply_text("🔐 Only admin can remove users.")
            return
        
        args = context.args
        if not args:
            await update.message.reply_text("📝 Please provide a user ID to remove.\n\n*Usage:* `/removeuser <user_id>`", parse_mode='Markdown')
            return
        
        remove_user_id = args[0]
        try:
            if self.user_manager.remove_user(remove_user_id):
                await update.message.reply_text(f"✅ User `{remove_user_id}` removed successfully.", parse_mode='Markdown')
            else:
                await update.message.reply_text(f"❌ Failed to remove user `{remove_user_id}`.", parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error removing user {remove_user_id}: {e}")
            await update.message.reply_text(f"❌ Error removing user: {str(e)}")

    async def _list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /list command"""
        if not await self._check_authorization(update):
            return
            
        args = context.args
        path = args[0] if args else "."
        try:
            files = self.file_operations.list_directory(path)
            if not files:
                await update.message.reply_text(f"📂 No files found in `{path}`", parse_mode='Markdown')
                return
                
            message = f"📂 *Files in {path}*\n\n"
            for file in files[:30]:  # Limit to 30 files to avoid message size limits
                message += f"• {file}\n"
            
            if len(files) > 30:
                message += f"\n... and {len(files) - 30} more files"
                
            await update.message.reply_text(message, parse_mode='Markdown')
        except FileNotFoundError as e:
            await update.message.reply_text(f"❌ Directory not found: `{path}`", parse_mode='Markdown')
        except NotADirectoryError as e:
            await update.message.reply_text(f"❌ Path is not a directory: `{path}`", parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error listing directory {path}: {e}")
            await update.message.reply_text(f"❌ Error listing directory: {str(e)}")

    async def _download_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /download command"""
        if not await self._check_authorization(update):
            return
            
        args = context.args
        if not args:
            await update.message.reply_text("📝 Please provide a file path.\n\n*Usage:* `/download <file_path>`", parse_mode='Markdown')
            return
            
        file_path = args[0]
        try:
            if self.file_operations.file_exists(file_path):
                full_path = os.path.join(self.file_operations.base_path, file_path)
                # Send the actual file
                await update.message.reply_document(document=open(full_path, 'rb'), filename=os.path.basename(file_path))
            else:
                await update.message.reply_text(f"❌ File not found: `{file_path}`", parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error downloading file {file_path}: {e}")
            await update.message.reply_text(f"❌ Error downloading file: {str(e)}")

    async def _delete_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /delete command"""
        if not await self._check_authorization(update):
            return
            
        args = context.args
        if not args:
            await update.message.reply_text("📝 Please provide a file path.\n\n*Usage:* `/delete <file_path>`", parse_mode='Markdown')
            return
            
        file_path = args[0]
        try:
            if self.file_operations.file_exists(file_path):
                self.file_operations.delete_file(file_path)
                await update.message.reply_text(f"🗑️ File deleted: `{file_path}`", parse_mode='Markdown')
            else:
                await update.message.reply_text(f"❌ File not found: `{file_path}`", parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            await update.message.reply_text(f"❌ Error deleting file: {str(e)}")

    async def _search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /search command"""
        if not await self._check_authorization(update):
            return
            
        args = context.args
        if not args:
            await update.message.reply_text("📝 Please provide a search query.\n\n*Usage:* `/search <query>`", parse_mode='Markdown')
            return
            
        query = ' '.join(args)
        try:
            results = self.file_operations.search_files(query, ".")
            if not results:
                await update.message.reply_text(f"🔍 No files found matching: `{query}`", parse_mode='Markdown')
                return
                
            message = f"🔍 *Search results for '{query}'*\n\n"
            for file in results[:15]:  # Limit to 15 files
                message += f"• {file}\n"
            
            if len(results) > 15:
                message += f"\n... and {len(results) - 15} more files"
                
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error searching for {query}: {e}")
            await update.message.reply_text(f"❌ Error searching files: {str(e)}")

    async def _status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        if not await self._check_authorization(update):
            return
            
        user_id = str(update.effective_user.id)
        is_admin = self.user_manager.is_admin(user_id)
        
        message = "✅ *Bot Status*\n\n"
        message += "📱 Bot is running and operational\n"
        
        if is_admin:
            # Add admin-specific status information
            users_count = len(self.user_manager.get_all_users())
            devices_count = len(self.device_manager.get_all_devices())
            message += f"\n📊 *Statistics*\n"
            message += f"• Users: {users_count}\n"
            message += f"• Devices: {devices_count}\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')

    async def _handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        if not await self._check_authorization(update):
            return
        await update.message.reply_text("📱 I only respond to commands. Type /help for available commands.")

    async def _echo_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /echo command for testing"""
        if not await self._check_authorization(update):
            return
            
        args = context.args
        if not args:
            await update.message.reply_text("📝 Please provide text to echo.\n\n*Usage:* `/echo <text>`", parse_mode='Markdown')
            return
            
        text = ' '.join(args)
        logger.info(f"Echoing text: {text}")
        await update.message.reply_text(f"🔁 Echo: {text}")
    async def _menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /menu command to show interactive menu"""
        if not await self._check_authorization(update):
            return
            
        user_id = str(update.effective_user.id)
        is_admin = self.user_manager.is_admin(user_id)
        
        message = "📱 *Flutter File Manager - Main Menu*\n\n"
        message += "📁 *File Operations*\n"
        message += "• /list <path> - List directory contents\n"
        message += "• /search <query> - Search for files\n"
        message += "• /download <file_path> - Download a file\n"
        message += "• /delete <file_path> - Delete a file\n\n"
        
        message += "📊 *Device Management*\n"
        message += "• /status - Show device status\n"
        
        if is_admin:
            message += "• /devices - List all registered devices\n\n"
            message += "👥 *User Management* (Admin only)\n"
            message += "• /users - List all authorized users\n"
            message += "• /adduser <user_id> - Add authorized user\n"
            message += "• /removeuser <user_id> - Remove authorized user\n\n"
        else:
            message += "\n"
            
        message += "ℹ️ *Help & Info*\n"
        message += "• /help - Show detailed help\n"
        message += "• /status - Bot status\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
            
        text = ' '.join(args)
        logger.info(f"Echoing text: {text}")
        await update.message.reply_text(f"🔁 Echo: {text}")