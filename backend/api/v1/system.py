from fastapi import APIRouter
from core.history_db import history_db
import platform
import psutil # Needs to be added to requirements
import os

router = APIRouter(prefix="/system", tags=["System"])

@router.get("/status")
def system_info():
    """Returns global system metrics (CPU, RAM, Rock 5C specific configs)"""
    return {
        "platform": platform.system(),
        "arch": platform.machine(),
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "temperature_c": None # Mocked for now, can be read from /sys/class/thermal
    }

@router.get("/history")
def get_logs(limit: int = 100, offset: int = 0):
    """Returns operations history"""
    return history_db.get_history(limit, offset)
