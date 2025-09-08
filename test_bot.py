#!/usr/bin/env python3
"""
Test script for the Telegram bot server
This script tests the basic functionality of the bot server components
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch
import json
import tempfile

# Add the bot directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from config import Config
from user_management import UserManager
from device_manager import DeviceManager
from file_operations import FileOperations
from utils import sanitize_input, validate_file_path

class TestConfig(unittest.TestCase):
    """Test the configuration management"""
    
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
    
    def test_config_defaults(self):
        """Test that config has sensible defaults"""
        config = Config()
        
        # These should have defaults
        self.assertIsNotNone(config.STORAGE_PATH)
        self.assertIsNotNone(config.ADMIN_ID)
        self.assertIsNotNone(config.PORT)
        
    def test_config_from_env(self):
        """Test that config can be loaded from environment variables"""
        # Set some test environment variables
        os.environ['BOT_TOKEN'] = 'test_token'
        os.environ['ADMIN_ID'] = '123456789'
        os.environ['STORAGE_PATH'] = self.test_dir
        
        config = Config()
        
        self.assertEqual(config.BOT_TOKEN, 'test_token')
        self.assertEqual(config.ADMIN_ID, '123456789')
        self.assertEqual(config.STORAGE_PATH, self.test_dir)
        
        # Clean up
        del os.environ['BOT_TOKEN']
        del os.environ['ADMIN_ID']
        del os.environ['STORAGE_PATH']

class TestUserManager(unittest.TestCase):
    """Test the user management functionality"""
    
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.user_manager = UserManager(self.test_dir)
    
    def test_add_user(self):
        """Test adding a user"""
        result = self.user_manager.add_user('123456789', 'admin')
        self.assertTrue(result)
        
        # Check that the user was added
        self.assertTrue(self.user_manager.is_authorized('123456789'))
        self.assertTrue(self.user_manager.is_admin('123456789'))
    
    def test_remove_user(self):
        """Test removing a user"""
        # Add a user first
        self.user_manager.add_user('123456789', 'user')
        self.assertTrue(self.user_manager.is_authorized('123456789'))
        
        # Remove the user
        result = self.user_manager.remove_user('123456789')
        self.assertTrue(result)
        
        # Check that the user was removed
        self.assertFalse(self.user_manager.is_authorized('123456789'))
    
    def test_get_all_users(self):
        """Test getting all users"""
        # Add a couple of users
        self.user_manager.add_user('123456789', 'admin')
        self.user_manager.add_user('987654321', 'user')
        
        users = self.user_manager.get_all_users()
        self.assertEqual(len(users), 2)
        self.assertIn('123456789', users)
        self.assertIn('987654321', users)

class TestDeviceManager(unittest.TestCase):
    """Test the device management functionality"""
    
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.device_manager = DeviceManager(self.test_dir)
    
    def test_register_device(self):
        """Test registering a device"""
        result = self.device_manager.register_device('device_123', 'Test Device')
        self.assertTrue(result)
        
        # Check that the device was registered
        device = self.device_manager.get_device('device_123')
        self.assertIsNotNone(device)
        self.assertEqual(device['device_name'], 'Test Device')
        self.assertTrue(device['online_status'])
    
    def test_get_all_devices(self):
        """Test getting all devices"""
        # Register a couple of devices
        self.device_manager.register_device('device_123', 'Test Device 1')
        self.device_manager.register_device('device_456', 'Test Device 2')
        
        devices = self.device_manager.get_all_devices()
        self.assertEqual(len(devices), 2)
        self.assertIn('device_123', devices)
        self.assertIn('device_456', devices)

class TestFileOperations(unittest.TestCase):
    """Test the file operations functionality"""
    
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.file_ops = FileOperations(self.test_dir)
        
        # Create some test files and directories
        os.makedirs(os.path.join(self.test_dir, 'test_dir'))
        with open(os.path.join(self.test_dir, 'test_file.txt'), 'w') as f:
            f.write('Test content')
    
    def test_list_directory(self):
        """Test listing directory contents"""
        entries = self.file_ops.list_directory('.')
        self.assertGreater(len(entries), 0)
        
        # Check that we have the expected entries
        entry_names = [entry.split()[1] for entry in entries]  # Extract file/dir names
        self.assertIn('test_dir/', entry_names)
        self.assertIn('test_file.txt', entry_names)
    
    def test_file_exists(self):
        """Test checking if a file exists"""
        self.assertTrue(self.file_ops.file_exists('test_file.txt'))
        self.assertFalse(self.file_ops.file_exists('nonexistent.txt'))
    
    def test_search_files(self):
        """Test searching for files"""
        # Create a test file with specific content
        with open(os.path.join(self.test_dir, 'search_test.txt'), 'w') as f:
            f.write('This is a test file for searching')
        
        results = self.file_ops.search_files('search')
        self.assertGreater(len(results), 0)
        
        # Check that our test file is in the results
        result_names = [result.split()[1] for result in results]  # Extract file names
        self.assertIn('search_test.txt', result_names)

class TestUtils(unittest.TestCase):
    """Test utility functions"""
    
    def test_sanitize_input(self):
        """Test input sanitization"""
        # Test normal input
        self.assertEqual(sanitize_input('normal input'), 'normal input')
        
        # Test input with null bytes
        self.assertEqual(sanitize_input('test\0input'), 'testinput')
        
        # Test very long input
        long_input = 'a' * 2000
        sanitized = sanitize_input(long_input)
        self.assertLessEqual(len(sanitized), 1000)
    
    def test_validate_file_path(self):
        """Test file path validation"""
        base_path = '/tmp'
        
        # Test valid path
        valid_path = 'test/file.txt'
        full_path = validate_file_path(valid_path, base_path)
        self.assertTrue(full_path.startswith(base_path))
        
        # Test path traversal attempt (this should raise an exception)
        with self.assertRaises(ValueError):
            validate_file_path('../etc/passwd', base_path)

if __name__ == '__main__':
    unittest.main()