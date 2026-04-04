from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

# Depending on the requested action, import the correct flasher
from core.vault_manager import vault_manager

router = APIRouter(prefix="/action", tags=["Actions"])

class FlashRequest(BaseModel):
    tool: str
    target: str
    firmware: str
    port: str = None
    baudrate: int = 921600

@router.post("/flash")
async def flash_single(request: FlashRequest):
    """Flashes a single device"""
    fw_path = vault_manager.get_firmware_path(request.target, request.firmware)
    if not fw_path:
        raise HTTPException(status_code=404, detail="Firmware not found")
        
    # Launch flasher directly (In production this might be long, so maybe trigger in bg or WS)
    # Using picotool as an example for RP2040
    if request.tool == "picotool":
        from core.flasher.picotool_runner import PicotoolRunner
        runner = PicotoolRunner()
        success = await runner.flash(fw_path)
        return {"status": "success" if success else "failed"}
    elif request.tool == "esptool":
        from core.flasher.esptool_runner import EspToolRunner
        runner = EspToolRunner()
        success = await runner.flash(fw_path, request.port, request.baudrate)
        return {"status": "success" if success else "failed"}
    else:
        raise HTTPException(status_code=400, detail=f"Tool {request.tool} unsupported.")
