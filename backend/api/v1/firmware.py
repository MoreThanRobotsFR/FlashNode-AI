from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from core.vault_manager import vault_manager
from typing import Dict, Any
import httpx
import os

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

@router.get("/{target}/{filename}/checksum")
async def get_checksum(target: str, filename: str) -> Dict[str, Any]:
    """Returns MD5 + SHA256 checksums for a specific firmware"""
    checksums = vault_manager.get_checksums(target, filename)
    if not checksums:
        raise HTTPException(status_code=404, detail="Firmware not found")
    return {
        "filename": filename,
        "target": target.upper(),
        "checksums": checksums
    }

@router.delete("/{target}/{filename}")
async def delete_firmware(target: str, filename: str) -> Dict[str, Any]:
    """Deletes a firmware from the vault"""
    success = vault_manager.delete_firmware(target, filename)
    if not success:
        raise HTTPException(status_code=404, detail="Firmware not found or could not be deleted")
    return {"status": "success"}

class FetchURLRequest(BaseModel):
    url: str
    target: str
    filename: str = None

@router.post("/fetch-url")
async def fetch_firmware_from_url(request: FetchURLRequest) -> Dict[str, Any]:
    """Downloads a firmware from a remote URL and stores it in the vault"""
    if request.target.upper() not in ["RP2040", "ESP32"]:
        raise HTTPException(status_code=400, detail="Invalid target. Must be RP2040 or ESP32.")
    
    # Derive filename from URL if not provided
    filename = request.filename or request.url.split("/")[-1].split("?")[0]
    if not filename:
        raise HTTPException(status_code=400, detail="Could not determine filename from URL. Please provide one.")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(request.url)
            response.raise_for_status()
            content = response.content
        
        checksums = vault_manager.save_firmware(request.target, filename, content)
        return {
            "status": "success",
            "filename": filename,
            "target": request.target.upper(),
            "size_bytes": len(content),
            "checksums": checksums
        }
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Remote server error: {e.response.status_code}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
