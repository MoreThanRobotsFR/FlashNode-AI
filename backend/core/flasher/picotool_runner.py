from .base import BaseFlasher

class PicotoolRunner(BaseFlasher):
    async def flash(self, firmware_path: str) -> bool:
        cmd = [
            "picotool",
            "load",
            "-x",
            firmware_path
        ]
        
        await self._emit_output(f"Starting picotool: {' '.join(cmd)}")
        return await self._run_command(cmd)

    async def _parse_output_for_progress(self, line: str):
        # Example output: "Loading into Flash: [==============================]  100%"
        if "Loading into Flash:" in line and "%" in line:
            try:
                # Naive parsing for percentage
                parts = line.split()
                for part in parts:
                    if "%" in part:
                        percentage = int(part.replace("%", ""))
                        await self._emit_progress(percentage, "Loading into Flash")
            except Exception:
                pass
