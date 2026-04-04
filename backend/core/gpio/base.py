from abc import ABC, abstractmethod

class GPIOBackend(ABC):
    @abstractmethod
    def set(self, pin_id: str, value: int):
        """Set a GPIO pin to HIGH (1) or LOW (0)"""
        pass

    @abstractmethod
    def get(self, pin_id: str) -> int:
        """Get the current state of a GPIO pin"""
        pass

    @abstractmethod
    def pulse(self, pin_id: str, duration_ms: int):
        """Pulse a target pin"""
        pass
