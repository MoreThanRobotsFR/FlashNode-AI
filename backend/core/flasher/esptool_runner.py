from .base import BaseFlasher
import re

class EspToolRunner(BaseFlasher):
    async def flash(self, firmware_path: str, port: str, baudrate: int = 921600, chip: str = "esp32", flash_address: str = "0x1000") -> bool:
        cmd = [
            "esptool.py",
            "--port", port,
            "--chip", chip,
            "--baud", str(baudrate),
            "--before", "default_reset",
            "--after", "hard_reset",
            "write_flash",
            "-z",
            "--flash_mode", "dio",
            "--flash_freq", "40m",
            "--flash_size", "detect",
            flash_address,
            firmware_path
        ]
        
        await self._emit_output(f"Starting esptool: {' '.join(cmd)}")
        return await self._run_command(cmd)

    async def _parse_output_for_progress(self, line: str):
        # Example output: "Writing at 0x00010000... (16 %)"
        match = re.search(r"Writing at .* \(([0-9]+) %\)", line)
        if match:
            percentage = int(match.group(1))
            await self._emit_progress(percentage, "Writing Flash")
        elif "Erasing flash..." in line:
            await self._emit_progress(0, "Erasing Flash")
        elif "Verifying just-written flash..." in line:
            await self._emit_progress(95, "Verifying")
