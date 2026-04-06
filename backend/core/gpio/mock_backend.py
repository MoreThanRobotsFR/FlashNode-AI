import logging
from .base import GPIOBackend
import time

logger = logging.getLogger(__name__)

class MockGPIOBackend(GPIOBackend):
    def __init__(self):
        self._state = {}
        logger.info("[MOCK GPIO] Backend initialized")

    def set(self, pin_id: str, value: int):
        self._state[pin_id] = value
        logger.info(f"[MOCK GPIO] {pin_id} -> {value}")

    def get(self, pin_id: str) -> int:
        value = self._state.get(pin_id, 0)
        logger.info(f"[MOCK GPIO] Read {pin_id}: {value}")
        return value

    def pulse(self, pin_id: str, duration_ms: int):
        logger.info(f"[MOCK GPIO] {pin_id} pulse {duration_ms}ms started")
        self.set(pin_id, 1)
        time.sleep(duration_ms / 1000.0)
        self.set(pin_id, 0)
        logger.info(f"[MOCK GPIO] {pin_id} pulse finished")

    @property
    def is_mock(self) -> bool:
        return True

    @property
    def backend_name(self) -> str:
        return "mock"

