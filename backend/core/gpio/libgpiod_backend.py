import json
import os
import logging
import time
from .base import GPIOBackend

logger = logging.getLogger(__name__)


class LibgpiodBackend(GPIOBackend):
    """
    GPIO backend using libgpiod v2 Python API (python3-gpiod >= 2.0).
    Tested with Rock 5C / Radxa boards running modern Linux kernels.

    Pin mapping is loaded from config/gpio_mapping.json.
    Each pin entry must have: id, chip (e.g. "/dev/gpiochip3"), offset (int), label (str), active ("high"|"low").
    """

    def __init__(self):
        self.gpiod = None
        self._lines = {}    # pin_id -> gpiod.LineRequest object
        self._state = {}    # pin_id -> current value (in-memory cache)
        self._pin_map = {}  # pin_id -> {chip, offset, active, label, gpio_name}

        try:
            import gpiod
            # Detect API version: v2 has gpiod.request_lines(), v1 has gpiod.Chip()
            if not hasattr(gpiod, 'request_lines'):
                raise ImportError(
                    "libgpiod v2 required (gpiod.request_lines not found). "
                    "Install python3-gpiod >= 2.0 or upgrade libgpiod."
                )
            self.gpiod = gpiod
            logger.info(f"libgpiod v2 module imported successfully (version: {getattr(gpiod, '__version__', 'unknown')})")
        except ImportError as e:
            logger.error(f"Failed to import gpiod v2: {e}")

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
                        "offset": int(pin["offset"]),
                        "active": pin.get("active", "high"),
                        "label": pin.get("label", pin["id"]),
                        "gpio_name": pin.get("gpio_name", "")
                    }
                logger.info(f"Loaded {len(self._pin_map)} GPIO pins from mapping config")
        except Exception as e:
            logger.error(f"Failed to load GPIO mapping: {e}")

    def _get_line(self, pin_id: str):
        """
        Get or request a gpiod v2 line for the given pin_id.
        Returns a gpiod.LineRequest object, or None on failure.
        """
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
            # gpiod v2 API: request_lines(chip, {offset: LineSettings})
            line_settings = self.gpiod.LineSettings(
                direction=self.gpiod.line.Direction.OUTPUT,
                output_value=self.gpiod.line.Value.INACTIVE,
            )
            request = self.gpiod.request_lines(
                chip_path,
                consumer="flashnode-ai",
                config={offset: line_settings}
            )
            self._lines[pin_id] = request
            self._state[pin_id] = 0
            logger.info(f"Requested GPIO line (v2): {pin_id} -> {chip_path}:{offset} ({pin_info['label']})")
            return request
        except Exception as e:
            logger.error(f"Failed to request GPIO line for {pin_id} ({chip_path}:{offset}): {e}")
            return None

    def _to_gpio_value(self, pin_id: str, int_value: int):
        """Convert integer 0/1 to gpiod v2 Value enum, respecting active-low config."""
        pin_info = self._pin_map.get(pin_id, {})
        active_low = pin_info.get("active", "high") == "low"
        # When active_low: writing 1 means INACTIVE (inverted)
        if active_low:
            int_value = 1 - int_value
        return self.gpiod.line.Value.ACTIVE if int_value else self.gpiod.line.Value.INACTIVE

    def set(self, pin_id: str, value: int):
        request = self._get_line(pin_id)
        pin_info = self._pin_map.get(pin_id, {})
        offset = pin_info.get("offset", -1)

        if request:
            try:
                gpio_val = self._to_gpio_value(pin_id, value)
                request.set_value(offset, gpio_val)
                self._state[pin_id] = value
                logger.info(f"GPIO {pin_id} ({pin_info.get('label', '?')}) -> {value}")
            except Exception as e:
                logger.error(f"Failed to set GPIO {pin_id}: {e}")
        else:
            # Dry-run fallback: update cache without hardware interaction
            self._state[pin_id] = value
            logger.warning(f"Dry-run set GPIO {pin_id} -> {value} (line not available)")

    def get(self, pin_id: str) -> int:
        request = self._get_line(pin_id)
        pin_info = self._pin_map.get(pin_id, {})
        offset = pin_info.get("offset", -1)

        if request:
            try:
                gpio_val = request.get_value(offset)
                # Convert gpiod.line.Value to int
                raw = 1 if gpio_val == self.gpiod.line.Value.ACTIVE else 0
                # Invert if active-low
                if pin_info.get("active", "high") == "low":
                    raw = 1 - raw
                self._state[pin_id] = raw
                return raw
            except Exception as e:
                logger.error(f"Failed to read GPIO {pin_id}: {e}")

        # Return cached state
        return self._state.get(pin_id, 0)

    def pulse(self, pin_id: str, duration_ms: int):
        self.set(pin_id, 1)
        time.sleep(duration_ms / 1000.0)
        self.set(pin_id, 0)

    def cleanup(self):
        """Release all GPIO line requests."""
        for pin_id, request in self._lines.items():
            try:
                request.release()
                logger.info(f"Released GPIO line: {pin_id}")
            except Exception:
                pass
        self._lines.clear()

    @property
    def is_mock(self) -> bool:
        return False

    @property
    def backend_name(self) -> str:
        return "libgpiod-v2"
