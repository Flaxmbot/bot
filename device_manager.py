import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DeviceManager:
    def __init__(self, storage_path):
        self.storage_path = storage_path
        self.devices_file = os.path.join(storage_path, 'devices.json')
        self.devices = self.load_devices()

    def load_devices(self):
        """Load devices from storage"""
        if os.path.exists(self.devices_file):
            try:
                with open(self.devices_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading devices: {e}")
                return {}
        return {}

    def save_devices(self):
        """Save devices to storage"""
        try:
            with open(self.devices_file, 'w') as f:
                json.dump(self.devices, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving devices: {e}")
            return False

    def register_device(self, device_id, device_name=None):
        """Register a new device"""
        self.devices[device_id] = {
            'device_id': device_id,
            'device_name': device_name or f"Device {device_id[:8]}",
            'registration_date': datetime.now().isoformat(),
            'last_seen': datetime.now().isoformat(),
            'online_status': True
        }
        return self.save_devices()

    def update_device_status(self, device_id, online=True):
        """Update device status"""
        if device_id in self.devices:
            self.devices[device_id]['last_seen'] = datetime.now().isoformat()
            self.devices[device_id]['online_status'] = online
            return self.save_devices()
        return False

    def get_device(self, device_id):
        """Get device information"""
        return self.devices.get(device_id)

    def get_all_devices(self):
        """Get all devices"""
        return self.devices

    def unregister_device(self, device_id):
        """Unregister a device"""
        if device_id in self.devices:
            del self.devices[device_id]
            return self.save_devices()
        return False