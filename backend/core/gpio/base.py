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

    @property
    def is_mock(self) -> bool:
        """Returns True if this backend is a mock (no real hardware)."""
        return False

    @property
    def backend_name(self) -> str:
        """Human-readable name of this backend."""
        return "unknown"
