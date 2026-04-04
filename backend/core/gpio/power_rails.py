from .factory import get_gpio_backend
import logging

logger = logging.getLogger(__name__)

class PowerRails:
    def __init__(self):
        self.backend = get_gpio_backend()
        # Read from config in a full implementation, hardcoded here as per pin IDs
        self.rail_5v_pin = "RAIL_5V"
        self.rail_3v3_pin = "RAIL_3V3"

    def power_on(self):
        """Safe power on sequence: 5V first, then 3.3V"""
        logger.info("Turning on power rails (5V then 3.3V)")
        self.backend.set(self.rail_5v_pin, 1)
        import time
        time.sleep(0.1)
        self.backend.set(self.rail_3v3_pin, 1)

    def power_off(self):
        """Safe power off sequence: 3.3V first, then 5V"""
        logger.info("Turning off power rails (3.3V then 5V)")
        self.backend.set(self.rail_3v3_pin, 0)
        import time
        time.sleep(0.1)
        self.backend.set(self.rail_5v_pin, 0)

    def power_cycle(self, off_duration_ms: int = 500):
        self.power_off()
        import time
        time.sleep(off_duration_ms / 1000.0)
        self.power_on()

    def get_status(self) -> dict:
        return {
            "5V": self.backend.get(self.rail_5v_pin) == 1,
            "3V3": self.backend.get(self.rail_3v3_pin) == 1
        }

power_rails = PowerRails()
