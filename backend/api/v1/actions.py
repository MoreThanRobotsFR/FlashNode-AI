from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import asyncio
import time

from core.vault_manager import vault_manager
from core.history_db import history_db
from ws.connection_manager import manager

router = APIRouter(prefix="/action", tags=["Actions"])

# ---- State ----
_current_action = {
    "status": "idle",
    "tool": None,
    "target": None,
    "firmware": None,
    "started_at": None,
    "progress": 0,
    "step": ""
}

def _set_action_state(status: str, tool: str = None, target: str = None, firmware: str = None):
    _current_action["status"] = status
    _current_action["tool"] = tool
    _current_action["target"] = target
    _current_action["firmware"] = firmware
    _current_action["started_at"] = time.time() if status == "running" else _current_action.get("started_at")
    _current_action["progress"] = 0 if status == "running" else _current_action["progress"]
    _current_action["step"] = ""


# ---- Flasher callbacks for WebSocket integration ----
async def _ws_output_callback(line: str):
    await manager.broadcast({"type": "stdout", "data": line}, channel="flash_output")

async def _ws_progress_callback(percentage: int, step: str):
    _current_action["progress"] = percentage
    _current_action["step"] = step
    await manager.broadcast({"progress": percentage, "step": step}, channel="flash_progress")


def _get_runner(tool: str):
    """Returns the correct flasher runner instance with WS callbacks"""
    if tool == "picotool":
        from core.flasher.picotool_runner import PicotoolRunner
        return PicotoolRunner(on_output=_ws_output_callback, on_progress=_ws_progress_callback)
    elif tool == "esptool":
        from core.flasher.esptool_runner import EspToolRunner
        return EspToolRunner(on_output=_ws_output_callback, on_progress=_ws_progress_callback)
    elif tool == "openocd":
        from core.flasher.openocd_runner import OpenOCDRunner
        return OpenOCDRunner(on_output=_ws_output_callback, on_progress=_ws_progress_callback)
    else:
        return None


# ---- Models ----
class FlashRequest(BaseModel):
    tool: str
    target: str
    firmware: str
    port: Optional[str] = None
    baudrate: int = 921600
    interface_cfg: str = "interface/cmsis-dap.cfg"
    target_cfg: str = "target/rp2040.cfg"
    adapter_speed: int = 5000

class EraseRequest(BaseModel):
    tool: str
    target: str
    port: Optional[str] = None

class VerifyRequest(BaseModel):
    tool: str
    target: str
    firmware: str
    port: Optional[str] = None

class ResetRequest(BaseModel):
    target: str


# ---- Endpoints ----
@router.post("/flash")
async def flash_single(request: FlashRequest):
    """Flashes a single device"""
    fw_path = vault_manager.get_firmware_path(request.target, request.firmware)
    if not fw_path:
        raise HTTPException(status_code=404, detail="Firmware not found")
    
    runner = _get_runner(request.tool)
    if not runner:
        raise HTTPException(status_code=400, detail=f"Tool {request.tool} unsupported.")
    
    _set_action_state("running", request.tool, request.target, request.firmware)
    start_time = time.time()
    
    try:
        if request.tool == "picotool":
            success = await runner.flash(fw_path)
        elif request.tool == "esptool":
            success = await runner.flash(fw_path, request.port or "/dev/ttyUSB0", request.baudrate)
        elif request.tool == "openocd":
            success = await runner.flash(fw_path, request.interface_cfg, request.target_cfg, request.adapter_speed)
        else:
            success = False
        
        duration = round(time.time() - start_time, 2)
        status = "SUCCESS" if success else "FAILED"
        _set_action_state(status.lower())
        history_db.log_operation(status, f"Flash {request.target} ({request.tool})", 
                                 target=request.firmware, duration_s=duration)
        return {"status": status.lower(), "duration_s": duration}
    except Exception as e:
        _set_action_state("error")
        history_db.log_operation("ERROR", f"Flash {request.target}", details=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/erase")
async def erase_flash(request: EraseRequest):
    """Erases the flash memory of a target device"""
    _set_action_state("running", request.tool, request.target)
    start_time = time.time()
    
    try:
        if request.tool == "esptool":
            cmd = ["esptool.py"]
            if request.port:
                cmd.extend(["--port", request.port])
            cmd.extend(["--chip", "auto", "erase_flash"])
            
            from core.flasher.base import BaseFlasher
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            stdout, _ = await process.communicate()
            output = stdout.decode('utf-8', errors='replace')
            await _ws_output_callback(output)
            success = process.returncode == 0
        elif request.tool == "picotool":
            # picotool doesn't have a dedicated erase, but we can load an empty binary
            # For now, return not supported
            raise HTTPException(status_code=501, detail="Erase via picotool not directly supported. Use flash with empty binary.")
        else:
            raise HTTPException(status_code=400, detail=f"Tool {request.tool} unsupported for erase.")
        
        duration = round(time.time() - start_time, 2)
        status = "SUCCESS" if success else "FAILED"
        _set_action_state(status.lower())
        history_db.log_operation(status, f"Erase {request.target} ({request.tool})", duration_s=duration)
        return {"status": status.lower(), "duration_s": duration}
    except HTTPException:
        raise
    except Exception as e:
        _set_action_state("error")
        history_db.log_operation("ERROR", f"Erase {request.target}", details=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify")
async def verify_flash(request: VerifyRequest):
    """Verifies firmware on device without re-flashing"""
    fw_path = vault_manager.get_firmware_path(request.target, request.firmware)
    if not fw_path:
        raise HTTPException(status_code=404, detail="Firmware not found")
    
    _set_action_state("running", request.tool, request.target, request.firmware)
    start_time = time.time()
    
    try:
        if request.tool == "esptool":
            cmd = ["esptool.py"]
            if request.port:
                cmd.extend(["--port", request.port])
            cmd.extend(["--chip", "auto", "verify_flash", fw_path])
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            stdout, _ = await process.communicate()
            output = stdout.decode('utf-8', errors='replace')
            await _ws_output_callback(output)
            success = process.returncode == 0
        elif request.tool == "openocd":
            cmd = [
                "openocd",
                "-f", "interface/cmsis-dap.cfg",
                "-f", "target/rp2040.cfg",
                "-c", f"verify_image {fw_path}",
                "-c", "exit"
            ]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            stdout, _ = await process.communicate()
            output = stdout.decode('utf-8', errors='replace')
            await _ws_output_callback(output)
            success = process.returncode == 0
        else:
            raise HTTPException(status_code=400, detail=f"Tool {request.tool} unsupported for verify.")
        
        duration = round(time.time() - start_time, 2)
        status = "SUCCESS" if success else "FAILED"
        _set_action_state(status.lower())
        history_db.log_operation(status, f"Verify {request.target} ({request.tool})", 
                                 target=request.firmware, duration_s=duration)
        return {"status": status.lower(), "duration_s": duration}
    except HTTPException:
        raise
    except Exception as e:
        _set_action_state("error")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_device(request: ResetRequest):
    """Performs a software/GPIO reset on the target device"""
    from core.gpio.sequences import sequence_runner
    
    target = request.target.upper()
    if target == "RP2040":
        success = await sequence_runner.run_sequence("rp2040_reset")
    elif target == "ESP32":
        success = await sequence_runner.run_sequence("esp32_reset")
    else:
        raise HTTPException(status_code=400, detail=f"Unknown target: {request.target}")
    
    history_db.log_operation("SUCCESS" if success else "FAILED", f"Reset {target}")
    return {"status": "success" if success else "failed", "target": target}


@router.get("/status")
async def get_action_status():
    """Returns the status of the current/last action"""
    result = dict(_current_action)
    if result["started_at"]:
        result["elapsed_s"] = round(time.time() - result["started_at"], 2)
    return result
