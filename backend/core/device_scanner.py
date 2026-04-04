import platform
import logging
from typing import List, Dict
import serial.tools.list_ports

logger = logging.getLogger(__name__)

class DeviceScanner:
    def __init__(self):
        self.is_linux = platform.system().lower() == "linux"
        try:
            if self.is_linux:
                import pyudev
                self.context = pyudev.Context()
            else:
                self.context = None
                logger.info("Non-linux system detected. USB scanning will be limited or mocked.")
        except ImportError:
            self.context = None
            logger.warning("pyudev not installed. USB scanning limited.")

    def scan_serial_ports(self) -> List[Dict]:
        """Returns a list of all serial ports available (Cross-platform)"""
        ports = []
        for port in serial.tools.list_ports.comports():
            # Guess device type based on vid/pid or description
            device_type = "Unknown"
            if port.vid == 0x2e8a:
                device_type = "RP2040 CDC"
            elif port.vid == 0x10c4:
                device_type = "ESP32 Programmer"
            elif "CP210" in port.description or "CH340" in port.description:
                device_type = "UART Adapter"

            ports.append({
                "port": port.device,
                "description": port.description,
                "hwid": port.hwid,
                "vid": hex(port.vid) if port.vid else None,
                "pid": hex(port.pid) if port.pid else None,
                "type": device_type
            })
        return ports

    def scan_usb_devices(self) -> List[Dict]:
        """Returns a list of USB devices, specifically targeting flash targets like RP2040 in BOOTSEL."""
        devices = []
        
        # If we are not on linux and don't have pyudev, we just return mocked/empty list 
        # or use a cross-platform alternative if available (we will just mock for PC dev for BOOTSEL).
        if not self.context:
            logger.info("Mocking USB device scan.")
            # For development, you can inject a mock RP2040 here if you want to test the UI
            """
            devices.append({
                "vendor_id": "2e8a",
                "product_id": "0003",
                "device_node": "/dev/sda",
                "description": "Raspberry Pi RP2 Boot (Mock)"
            })
            """
            return devices

        try:
            # We are on linux with pyudev
            for device in self.context.list_devices(subsystem='usb', DEVTYPE='usb_device'):
                vid = device.properties.get('ID_VENDOR_ID')
                pid = device.properties.get('ID_MODEL_ID')
                
                if vid and pid:
                    description = device.properties.get('ID_MODEL_FROM_DATABASE', 'USB Device')
                    if vid == '2e8a' and pid == '0003':
                        description = "Raspberry Pi RP2 Boot"
                        
                    devices.append({
                        "vendor_id": vid,
                        "product_id": pid,
                        "device_node": device.device_node,
                        "description": description
                    })
        except Exception as e:
            logger.error(f"Failed to scan USB devices: {e}")
            
        return devices

device_scanner = DeviceScanner()
