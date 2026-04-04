import os
import platform
from .base import GPIOBackend

_backend_instance = None

def get_gpio_backend() -> GPIOBackend:
    global _backend_instance
    if _backend_instance is not None:
        return _backend_instance

    # Permet de forcer un backend via variable d'environnement (ex: GPIO_BACKEND=mock)
    forced_backend = os.environ.get("GPIO_BACKEND", "").lower()
    
    # Par défaut, aarch64 (ARM 64-bit) sur Linux utilise la vraie libgpiod.
    # Tout autre environnement utilise le mock par défaut.
    use_mock = True
    
    if forced_backend == "mock":
        use_mock = True
    elif forced_backend == "libgpiod":
        use_mock = False
    elif platform.machine() == "aarch64" and platform.system().lower() == "linux":
        use_mock = False

    if use_mock:
        from .mock_backend import MockGPIOBackend
        _backend_instance = MockGPIOBackend()
    else:
        from .libgpiod_backend import LibgpiodBackend
        _backend_instance = LibgpiodBackend()

    return _backend_instance
