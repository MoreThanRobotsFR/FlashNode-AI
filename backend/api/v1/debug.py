from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter(prefix="/debug", tags=["Debug"])

@router.post("/start")
def start_debug_session():
    return {"status": "mocked", "detail": "GDB/OpenOCD debug session started"}

@router.post("/stop")
def stop_debug_session():
    return {"status": "mocked", "detail": "GDB/OpenOCD debug session stopped"}

@router.get("/status")
def debug_status():
    return {"status": "stopped"}
