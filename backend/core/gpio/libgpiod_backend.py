from .base import GPIOBackend

import logging

logger = logging.getLogger(__name__)

class LibgpiodBackend(GPIOBackend):
    def __init__(self):
        try:
            import gpiod
            self.gpiod = gpiod
            logger.info("libgpiod backend initialized successfully")
        except ImportError:
            logger.error("Failed to import gpiod. Ensure python3-gpiod is installed on your system.")
            self.gpiod = None

    def set(self, pin_id: str, value: int):
        if not self.gpiod:
            logger.warning(f"Mocking set for {pin_id}={value} because gpiod is not available")
            return
            
        # TODO: Implémentation réelle libgpiod pour le Rock 5C
        # Il faudra parser pin_id, trouver le gpiochip, demander la ligne et set la valeur.
        logger.info(f"Setting real GPIO {pin_id} to {value}")

    def get(self, pin_id: str) -> int:
        if not self.gpiod:
            logger.warning(f"Mocking get for {pin_id} because gpiod is not available")
            return 0
            
        # TODO: Implémentation réelle libgpiod
        return 0

    def pulse(self, pin_id: str, duration_ms: int):
        import time
        self.set(pin_id, 1)
        time.sleep(duration_ms / 1000.0)
        self.set(pin_id, 0)
