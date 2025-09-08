import os
import logging
import hashlib
import secrets

logger = logging.getLogger(__name__)

def generate_device_id():
    """Generate a unique device ID"""
    return secrets.token_urlsafe(16)

def validate_file_path(path, base_path="/"):
    """Validate file path to prevent directory traversal"""
    # Resolve the absolute path
    full_path = os.path.abspath(os.path.join(base_path, path))
    base_path = os.path.abspath(base_path)
    
    # Check if the path is within the base path
    if not full_path.startswith(base_path):
        raise ValueError("File path is outside allowed directory")
    
    return full_path

def sanitize_input(text):
    """Sanitize user input"""
    if not isinstance(text, str):
        return ""
    
    # Remove null bytes
    text = text.replace('\0', '')
    
    # Limit length
    text = text[:1000]
    
    return text

def hash_token(token):
    """Hash a token for secure storage"""
    return hashlib.sha256(token.encode()).hexdigest()

def setup_logging(level=logging.INFO):
    """Setup logging configuration"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('bot.log')
        ]
    )