import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class UserManager:
    def __init__(self, storage_path):
        self.storage_path = storage_path
        self.users_file = os.path.join(storage_path, 'users.json')
        self.users = self.load_users()

    def load_users(self):
        """Load users from storage"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading users: {e}")
                return {}
        return {}

    def save_users(self):
        """Save users to storage"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving users: {e}")
            return False

    def add_user(self, user_id, role='user'):
        """Add a new user"""
        user_id = str(user_id)
        self.users[user_id] = {
            'role': role,
            'registration_date': datetime.now().isoformat(),
            'last_active': datetime.now().isoformat(),
            'active': True
        }
        return self.save_users()

    def remove_user(self, user_id):
        """Remove a user"""
        user_id = str(user_id)
        if user_id in self.users:
            del self.users[user_id]
            return self.save_users()
        return False

    def is_authorized(self, user_id):
        """Check if user is authorized"""
        user_id = str(user_id)
        logger.info(f"Checking if user {user_id} is authorized")
        logger.info(f"Current users: {self.users}")
        result = user_id in self.users and self.users[user_id].get('active', False)
        logger.info(f"Authorization result for user {user_id}: {result}")
        return result

    def is_admin(self, user_id):
        """Check if user is admin"""
        user_id = str(user_id)
        return (user_id in self.users and 
                self.users[user_id].get('role') == 'admin' and 
                self.users[user_id].get('active', False))

    def update_last_active(self, user_id):
        """Update user's last active timestamp"""
        user_id = str(user_id)
        if user_id in self.users:
            self.users[user_id]['last_active'] = datetime.now().isoformat()
            return self.save_users()
        return False

    def get_all_users(self):
        """Get all users"""
        return self.users

    def deactivate_user(self, user_id):
        """Deactivate a user"""
        user_id = str(user_id)
        if user_id in self.users:
            self.users[user_id]['active'] = False
            return self.save_users()
        return False