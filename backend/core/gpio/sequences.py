import json
import os
import time
import asyncio
import logging
from .factory import get_gpio_backend

logger = logging.getLogger(__name__)


class SequenceRunner:
    def __init__(self):
        self.backend = get_gpio_backend()
        self.sequences = self._load_sequences()

    def _load_sequences(self) -> dict:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        config_path = os.path.join(base_dir, "config", "gpio_sequences.json")
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load sequences from {config_path}: {e}")
            return {}

    async def run_sequence(self, sequence_name: str, restore: bool = False) -> dict:
        """
        Run a named GPIO sequence.

        Returns a dict:
          {
            "success": bool,
            "sequence": str,
            "dry_run": bool,       # True if running against mock GPIO backend
            "steps_executed": int,
            "error": str or None
          }
        """
        is_mock = getattr(self.backend, 'is_mock', False)

        if sequence_name not in self.sequences:
            logger.error(f"Sequence '{sequence_name}' not found")
            return {"success": False, "sequence": sequence_name, "dry_run": is_mock, "steps_executed": 0, "error": f"Sequence '{sequence_name}' not found"}

        seq_def = self.sequences[sequence_name]
        steps = seq_def.get("restore_after_flash" if restore else "steps", [])

        logger.info(f"Running sequence: {sequence_name} (restore={restore}, dry_run={is_mock})")

        step_count = 0
        try:
            for step in steps:
                if "pin" in step and "value" in step:
                    self.backend.set(step["pin"], step["value"])
                    step_count += 1
                elif "action" in step and step["action"] == "wait_usb":
                    await asyncio.sleep(step.get("timeout_ms", 1000) / 1000.0)
                    step_count += 1

                delay = step.get("delay_after_ms", 0)
                if delay > 0:
                    await asyncio.sleep(delay / 1000.0)

        except Exception as e:
            logger.error(f"Sequence '{sequence_name}' failed at step {step_count}: {e}")
            return {"success": False, "sequence": sequence_name, "dry_run": is_mock, "steps_executed": step_count, "error": str(e)}

        return {"success": True, "sequence": sequence_name, "dry_run": is_mock, "steps_executed": step_count, "error": None}


sequence_runner = SequenceRunner()
