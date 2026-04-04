from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from core.vault_manager import vault_manager
from typing import Dict, Any

router = APIRouter(prefix="/firmware", tags=["Firmwares"])

@router.post("/upload")
async def upload_firmware(target: str = Form(...), file: UploadFile = File(...)) -> Dict[str, Any]:
    """Uploads a firmware to the vault"""
    if target.upper() not in ["RP2040", "ESP32"]:
        raise HTTPException(status_code=400, detail="Invalid target. Must be RP2040 or ESP32.")
        
    try:
        content = await file.read()
        checksums = vault_manager.save_firmware(target, file.filename, content)
        return {
            "status": "success",
            "filename": file.filename,
            "target": target.upper(),
            "checksums": checksums
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_firmwares() -> Dict[str, Any]:
    """Lists all firmwares in the vault by target"""
    return vault_manager.list_firmwares()
