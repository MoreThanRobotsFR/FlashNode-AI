from .base import BaseFlasher

class OpenOCDRunner(BaseFlasher):
    async def flash(self, firmware_path: str, interface_cfg: str = "interface/cmsis-dap.cfg", target_cfg: str = "target/rp2040.cfg", adapter_speed: int = 5000) -> bool:
        cmd = [
            "openocd",
            "-f", interface_cfg,
            "-f", target_cfg,
            "-c", f"adapter speed {adapter_speed}",
            "-c", f"program {firmware_path} verify reset exit"
        ]
        
        await self._emit_output(f"Starting OpenOCD: {' '.join(cmd)}")
        return await self._run_command(cmd)

    async def _parse_output_for_progress(self, line: str):
        # OpenOCD output is sometimes tricky, typical output:
        # "** Programming Started **"
        # "** Programming Finished **"
        # "** Verify Started **"
        # "** Verified OK **"
        
        if "** Programming Started **" in line:
            await self._emit_progress(10, "Programming")
        elif "** Programming Finished **" in line:
            await self._emit_progress(50, "Programming OK")
        elif "** Verify Started **" in line:
            await self._emit_progress(60, "Verifying")
        elif "** Verified OK **" in line:
            await self._emit_progress(95, "Verify OK")
