import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Callable, Awaitable, Optional

logger = logging.getLogger(__name__)

class BaseFlasher(ABC):
    def __init__(self, 
                 on_output: Optional[Callable[[str], Awaitable[None]]] = None,
                 on_progress: Optional[Callable[[int, str], Awaitable[None]]] = None):
        self.on_output = on_output
        self.on_progress = on_progress

    async def _emit_output(self, line: str):
        if self.on_output:
            await self.on_output(line)
        logger.debug(f"[FLASHER] {line}")

    async def _emit_progress(self, percentage: int, step: str):
        if self.on_progress:
            await self.on_progress(percentage, step)

    async def _run_command(self, cmd: list) -> bool:
        """Runs a command and streams its output"""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )

            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                    
                decoded_line = line.decode('utf-8', errors='replace').strip()
                await self._emit_output(decoded_line)
                await self._parse_output_for_progress(decoded_line)

            await process.wait()
            
            if process.returncode == 0:
                await self._emit_progress(100, "Done")
                return True
            else:
                await self._emit_output(f"Error: Process exited with code {process.returncode}")
                return False

        except Exception as e:
            await self._emit_output(f"Execution Error: {str(e)}")
            return False

    @abstractmethod
    async def flash(self, firmware_path: str, **kwargs) -> bool:
        """Execute the flashing process"""
        pass
        
    @abstractmethod
    async def _parse_output_for_progress(self, line: str):
        """Parse tool-specific output to emit progress events"""
        pass
