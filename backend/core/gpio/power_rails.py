from .factory import get_gpio_backend
import asyncio
import logging
import time

logger = logging.getLogger(__name__)

class PowerRails:
    def __init__(self):
        self.backend = get_gpio_backend()
        self.rail_5v_pin = "RAIL_5V"
        self.rail_3v3_pin = "RAIL_3V3"

    def power_on(self):
        """Safe power on sequence: 5V first, then 3.3V"""
        logger.info("Turning on power rails (5V then 3.3V)")
        self.backend.set(self.rail_5v_pin, 1)
        time.sleep(0.1)
        self.backend.set(self.rail_3v3_pin, 1)

    def power_off(self):
        """Safe power off sequence: 3.3V first, then 5V"""
        logger.info("Turning off power rails (3.3V then 5V)")
        self.backend.set(self.rail_3v3_pin, 0)
        time.sleep(0.1)
        self.backend.set(self.rail_5v_pin, 0)

    def power_cycle(self, off_duration_ms: int = 500):
        """Synchronous power cycle — use power_cycle_async in async contexts."""
        self.power_off()
        time.sleep(off_duration_ms / 1000.0)
        self.power_on()

    async def power_cycle_async(self, off_duration_ms: int = 500):
        """Non-blocking power cycle safe for asyncio event loops."""
        await asyncio.to_thread(self.power_off)
        await asyncio.sleep(off_duration_ms / 1000.0)
        await asyncio.to_thread(self.power_on)

    async def set_rail_async(self, rail: str, state: bool):
        """Async-safe rail control."""
        pin = self.rail_5v_pin if rail.lower() in ("5v", "5V") else self.rail_3v3_pin
        await asyncio.to_thread(self.backend.set, pin, 1 if state else 0)

    def get_status(self) -> dict:
        return {
            "5V": self.backend.get(self.rail_5v_pin) == 1,
            "3V3": self.backend.get(self.rail_3v3_pin) == 1
        }

power_rails = PowerRails()
