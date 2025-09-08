# Running Tests for the Telegram Bot Server

This document explains how to run tests for the Telegram bot server components.

## Prerequisites

Before running tests, ensure you have the required dependencies installed:

```bash
pip install -r requirements.txt
```

## Running Tests

### Run All Tests

To run all tests, execute the test script:

```bash
python test_bot.py
```

### Run Specific Test Classes

You can run specific test classes using the unittest module:

```bash
# Run only Config tests
python -m unittest test_bot.TestConfig

# Run only User Manager tests
python -m unittest test_bot.TestUserManager

# Run only Device Manager tests
python -m unittest test_bot.TestDeviceManager

# Run only File Operations tests
python -m unittest test_bot.TestFileOperations

# Run only Utility tests
python -m unittest test_bot.TestUtils
```

### Run Individual Test Methods

You can also run individual test methods:

```bash
# Run a specific test method
python -m unittest test_bot.TestUserManager.test_add_user
```

### Run Tests with Verbose Output

For more detailed output, use the verbose flag:

```bash
python test_bot.py -v
```

## Test Coverage

The test suite covers the following components:

1. **Config Tests** (`TestConfig`)
   - Configuration loading from environment variables
   - Default value handling
   - Configuration validation

2. **User Management Tests** (`TestUserManager`)
   - Adding and removing users
   - User authorization checks
   - Admin privilege verification
   - User data persistence

3. **Device Management Tests** (`TestDeviceManager`)
   - Device registration
   - Device status updates
   - Device data retrieval
   - Device data persistence

4. **File Operations Tests** (`TestFileOperations`)
   - Directory listing
   - File existence checking
   - File search functionality
   - File size formatting

5. **Utility Tests** (`TestUtils`)
   - Input sanitization
   - File path validation
   - Security functions

## Continuous Integration

For continuous integration, you can run tests as part of your deployment pipeline:

```bash
# Run tests and exit with error code if any fail
python -m unittest test_bot.TestConfig test_bot.TestUserManager test_bot.TestDeviceManager test_bot.TestFileOperations test_bot.TestUtils
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Make sure you're running tests from the bot directory
   - Ensure all required dependencies are installed

2. **Permission Errors**
   - Tests create temporary files; ensure you have write permissions
   - On some systems, you may need to run tests with elevated privileges

3. **Network Errors**
   - Some tests may require internet connectivity
   - Ensure your firewall isn't blocking test connections

### Debugging Test Failures

To debug test failures, you can:

1. Run tests with verbose output:
   ```bash
   python test_bot.py -v
   ```

2. Run a single test with maximum verbosity:
   ```bash
   python -m unittest test_bot.TestConfig.test_config_defaults -v
   ```

3. Add print statements to the test code to debug specific issues

## Adding New Tests

To add new tests:

1. Add new test methods to the appropriate test class in [test_bot.py](file:///e:/flutterfile_manager_pro/bot/test_bot.py)
2. Follow the existing naming convention (`test_` prefix)
3. Use assertions to verify expected behavior
4. Run the tests to ensure they pass

Example of adding a new test:

```python
class TestUserManager(unittest.TestCase):
    # ... existing tests ...
    
    def test_user_last_active_update(self):
        """Test updating user's last active timestamp"""
        # Add a user
        self.user_manager.add_user('123456789', 'user')
        
        # Update last active time
        result = self.user_manager.update_last_active('123456789')
        self.assertTrue(result)
        
        # Verify the update
        users = self.user_manager.get_all_users()
        self.assertIn('123456789', users)
        self.assertIn('last_active', users['123456789'])
```