import os
from utils import hash_token

class Config:
    """Configuration management for the bot"""
    
    def __init__(self):
        # Bot configuration
        self.BOT_TOKEN = os.environ.get('BOT_TOKEN')
        self.ADMIN_ID = os.environ.get('ADMIN_ID', '5445671392')
        self.STORAGE_PATH = os.environ.get('STORAGE_PATH', '/tmp/bot_storage')
        self.PORT = int(os.environ.get('PORT', 8080))
        
        # Security configuration
        self.RATE_LIMIT = int(os.environ.get('RATE_LIMIT', 10))  # Messages per minute
        self.MAX_FILE_SIZE = int(os.environ.get('MAX_FILE_SIZE', 50 * 1024 * 1024))  # 50MB default
        
        # Feature flags
        self.ENABLE_FILE_UPLOAD = os.environ.get('ENABLE_FILE_UPLOAD', 'true').lower() == 'true'
        self.ENABLE_FILE_DOWNLOAD = os.environ.get('ENABLE_FILE_DOWNLOAD', 'true').lower() == 'true'
        self.ENABLE_FILE_DELETE = os.environ.get('ENABLE_FILE_DELETE', 'false').lower() == 'true'
        
    @property
    def bot_token_hash(self):
        """Get hashed bot token for secure logging"""
        if self.BOT_TOKEN:
            return hash_token(self.BOT_TOKEN)
        return None
        
    def validate(self):
        """Validate configuration"""
        errors = []
        
        if not self.BOT_TOKEN:
            errors.append("BOT_TOKEN environment variable is required")
            
        if not self.ADMIN_ID:
            errors.append("ADMIN_ID environment variable is required")
            
        if not os.path.exists(self.STORAGE_PATH):
            try:
                os.makedirs(self.STORAGE_PATH, exist_ok=True)
            except Exception as e:
                errors.append(f"Unable to create storage path {self.STORAGE_PATH}: {e}")
                
        return errors