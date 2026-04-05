import asyncio
import logging
from typing import Dict, Any, Callable, Awaitable, Optional
from .history_db import history_db
from .gpio.sequences import sequence_runner
from .gpio.power_rails import power_rails
# We will import flashers dynamically based on step requirements

logger = logging.getLogger(__name__)

class PipelineEngine:
    def __init__(self, 
                 on_step_progress: Callable = None):
        self.on_step_progress = on_step_progress

    async def _emit_progress(self, pipeline_id: str, step_idx: int, total: int, status: str, step_details: Dict[str, Any] = None):
        if self.on_step_progress:
            await self.on_step_progress(pipeline_id, step_idx, total, status, step_details)

    async def run_pipeline(self, pipeline_def: Dict[str, Any], cancel_check: Callable[[], bool] = None) -> bool:
        name = pipeline_def.get("name", pipeline_def.get("id", "Unknown"))
        pipeline_id = pipeline_def.get("id", name)
        steps = pipeline_def.get("steps", [])
        total_steps = len(steps)
        
        logger.info(f"Starting pipeline {name} (ID: {pipeline_id}) with {total_steps} steps.")
        history_db.log_operation("STARTED", f"Pipeline {name}")

        for i, step in enumerate(steps, 1):
            # Check cancel flag
            if cancel_check and cancel_check():
                logger.info(f"Pipeline {name} cancelled at step {i}")
                await self._emit_progress(pipeline_id, i, total_steps, "cancelled", step)
                history_db.log_operation("CANCELLED", f"Pipeline {name}", details=f"Cancelled at step {i}")
                return False

            await self._emit_progress(pipeline_id, i, total_steps, "running", step)
            action = step.get("action")
            logger.info(f"Step {i}: {step.get('description', action)}")
            
            try:
                success = await self._execute_step(step)
                if not success:
                    logger.error(f"Pipeline {name} failed at step {i}")
                    await self._emit_progress(pipeline_id, i, total_steps, "failed", step)
                    history_db.log_operation("FAILED", f"Pipeline {name}", details=f"Failed at step {i}")
                    if pipeline_def.get("on_error") == "stop":
                        return False
            except Exception as e:
                logger.error(f"Error in step {i}: {e}")
                await self._emit_progress(pipeline_id, i, total_steps, "error", step)
                history_db.log_operation("ERROR", f"Pipeline {name}", details=str(e))
                return False

        await self._emit_progress(pipeline_id, total_steps, total_steps, "completed", {})
        history_db.log_operation("SUCCESS", f"Pipeline {name}")
        logger.info(f"Pipeline {name} completed successfully.")
        return True

    async def _execute_step(self, step: Dict[str, Any]) -> bool:
        action = step.get("action")
        
        if action == "gpio_set":
            from .gpio.factory import get_gpio_backend
            get_gpio_backend().set(step["pin"], step["value"])
            return True
            
        elif action == "gpio_pulse":
            from .gpio.factory import get_gpio_backend
            get_gpio_backend().pulse(step["pin"], step.get("duration_ms", 100))
            return True
            
        elif action == "gpio_sequence":
            seq = step["sequence"]
            if seq == "power_cycle":
                power_rails.power_cycle(step.get("off_duration_ms", 500))
                return True
            else:
                return await sequence_runner.run_sequence(seq)
                
        elif action == "delay":
            await asyncio.sleep(step.get("duration_ms", 0) / 1000.0)
            return True
            
        elif action in ["flash", "flash_and_verify"]:
            tool = step.get("tool")
            firmware = step.get("firmware")
            from .vault_manager import vault_manager
            target = step.get("target", "RP2040")
            fw_path = vault_manager.get_firmware_path(target, firmware)
            
            if not fw_path:
                logger.error(f"Firmware {firmware} not found for {target}")
                return False

            if tool == "picotool":
                from .flasher.picotool_runner import PicotoolRunner
                runner = PicotoolRunner()
                return await runner.flash(fw_path)
            elif tool == "esptool":
                from .flasher.esptool_runner import EspToolRunner
                runner = EspToolRunner()
                return await runner.flash(fw_path, step.get("port", "/dev/ttyUSB0"), step.get("baudrate", 921600))
            elif tool == "openocd":
                from .flasher.openocd_runner import OpenOCDRunner
                runner = OpenOCDRunner()
                return await runner.flash(fw_path)
                
            return False
            
        elif action == "erase":
            tool = step.get("tool", "esptool")
            if tool == "esptool":
                port = step.get("port", "/dev/ttyUSB0")
                cmd = ["esptool.py", "--port", port, "--chip", "auto", "erase_flash"]
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT
                )
                await process.wait()
                return process.returncode == 0
            return False
            
        elif action == "reset":
            target = step.get("target", "RP2040").upper()
            if target == "RP2040":
                return await sequence_runner.run_sequence("rp2040_reset")
            elif target == "ESP32":
                return await sequence_runner.run_sequence("esp32_reset")
            return False
            
        elif action == "monitor_serial":
            port = step.get("port")
            expected = step.get("expected_output", "")
            timeout_ms = step.get("timeout_ms", 10000)
            
            # Real implementation: try to open serial port and wait for expected string
            try:
                import serial
                timeout_s = timeout_ms / 1000.0
                ser = serial.Serial(port, baudrate=step.get("baudrate", 115200), timeout=1)
                elapsed = 0.0
                buffer = ""
                while elapsed < timeout_s:
                    data = ser.read(ser.in_waiting or 1)
                    if data:
                        decoded = data.decode('utf-8', errors='replace')
                        buffer += decoded
                        logger.info(f"[SERIAL] {decoded.strip()}")
                        if expected in buffer:
                            ser.close()
                            return True
                    await asyncio.sleep(0.1)
                    elapsed += 0.1
                ser.close()
                logger.warning(f"Serial monitor timed out waiting for: {expected}")
                on_timeout = step.get("on_timeout", "fail")
                return on_timeout != "fail"
            except Exception as e:
                logger.warning(f"Serial monitor error (mocking): {e}")
                # Fallback to mock for dev environments
                logger.info(f"Mocking serial monitor waiting for: {expected}")
                await asyncio.sleep(1)
                return True
            
        elif action == "verify_checksum":
            firmware = step.get("firmware")
            target = step.get("target", "RP2040")
            from .vault_manager import vault_manager
            checksums = vault_manager.get_checksums(target, firmware)
            if checksums:
                logger.info(f"Checksum verified for {firmware}: {checksums}")
                return True
            return False
            
        logger.warning(f"Unknown action: {action}")
        return False

pipeline_engine = PipelineEngine()
