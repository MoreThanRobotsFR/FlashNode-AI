from .base import GPIOBackend
import time

class MockGPIOBackend(GPIOBackend):
    def __init__(self):
        self._state = {}
        print("[MOCK GPIO] Backend initialized")

    def set(self, pin_id: str, value: int):
        self._state[pin_id] = value
        print(f"[MOCK GPIO] {pin_id} → {value}")

    def get(self, pin_id: str) -> int:
        value = self._state.get(pin_id, 0)
        print(f"[MOCK GPIO] Read {pin_id}: {value}")
        return value

    def pulse(self, pin_id: str, duration_ms: int):
        print(f"[MOCK GPIO] {pin_id} pulse {duration_ms}ms started")
        self.set(pin_id, 1)
        time.sleep(duration_ms / 1000.0)
        self.set(pin_id, 0)
        print(f"[MOCK GPIO] {pin_id} pulse finished")
