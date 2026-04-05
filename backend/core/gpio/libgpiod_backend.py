from .base import GPIOBackend

import json
import os
import logging
import time

logger = logging.getLogger(__name__)

class LibgpiodBackend(GPIOBackend):
    def __init__(self):
        self.gpiod = None
        self._lines = {}     # pin_id -> gpiod Line object
        self._state = {}     # pin_id -> current value (cache)
        self._pin_map = {}   # pin_id -> {"chip": str, "offset": int, "active": str, ...}
        
        try:
            import gpiod
            self.gpiod = gpiod
            logger.info("libgpiod module imported successfully")
        except ImportError:
            logger.error("Failed to import gpiod. Ensure python3-gpiod is installed on your system.")
        
        self._load_pin_mapping()
    
    def _load_pin_mapping(self):
        """Load pin mapping from config/gpio_mapping.json"""
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        config_path = os.path.join(base_dir, "config", "gpio_mapping.json")
        
        try:
            with open(config_path, "r") as f:
                data = json.load(f)
                for pin in data.get("pins", []):
                    self._pin_map[pin["id"]] = {
                        "chip": pin["chip"],
                        "offset": pin["offset"],
                        "active": pin.get("active", "high"),
                        "label": pin.get("label", pin["id"]),
                        "gpio_name": pin.get("gpio_name", "")
                    }
                logger.info(f"Loaded {len(self._pin_map)} GPIO pins from mapping config")
        except Exception as e:
            logger.error(f"Failed to load GPIO mapping: {e}")

    def _get_line(self, pin_id: str):
        """Get or request a gpiod line for the given pin_id"""
        if not self.gpiod:
            logger.warning(f"gpiod not available, cannot access pin {pin_id}")
            return None
        
        if pin_id in self._lines:
            return self._lines[pin_id]
        
        if pin_id not in self._pin_map:
            logger.error(f"Pin {pin_id} not found in gpio_mapping.json")
            return None
        
        pin_info = self._pin_map[pin_id]
        chip_path = pin_info["chip"]
        offset = pin_info["offset"]
        
        try:
            chip = self.gpiod.Chip(chip_path)
            line = chip.get_line(offset)
            line.request(
                consumer="flashnode-ai",
                type=self.gpiod.LINE_REQ_DIR_OUT,
                default_vals=[0]
            )
            self._lines[pin_id] = line
            self._state[pin_id] = 0
            logger.info(f"Requested GPIO line: {pin_id} -> {chip_path}:{offset} ({pin_info['label']})")
            return line
        except Exception as e:
            logger.error(f"Failed to request GPIO line for {pin_id} ({chip_path}:{offset}): {e}")
            return None

    def set(self, pin_id: str, value: int):
        line = self._get_line(pin_id)
        if line:
            try:
                line.set_value(value)
                self._state[pin_id] = value
                logger.info(f"GPIO {pin_id} ({self._pin_map.get(pin_id, {}).get('label', '?')}) -> {value}")
            except Exception as e:
                logger.error(f"Failed to set GPIO {pin_id}: {e}")
        else:
            # Fallback: log that we would have set the pin
            self._state[pin_id] = value
            logger.warning(f"Dry-run set GPIO {pin_id} -> {value} (line not available)")

    def get(self, pin_id: str) -> int:
        line = self._get_line(pin_id)
        if line:
            try:
                value = line.get_value()
                self._state[pin_id] = value
                return value
            except Exception as e:
                logger.error(f"Failed to read GPIO {pin_id}: {e}")
        
        # Return cached state
        return self._state.get(pin_id, 0)

    def pulse(self, pin_id: str, duration_ms: int):
        self.set(pin_id, 1)
        time.sleep(duration_ms / 1000.0)
        self.set(pin_id, 0)
    
    def cleanup(self):
        """Release all GPIO lines"""
        for pin_id, line in self._lines.items():
            try:
                line.release()
                logger.info(f"Released GPIO line: {pin_id}")
            except Exception:
                pass
        self._lines.clear()
