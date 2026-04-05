from fastapi import APIRouter
from core.history_db import history_db
import platform
import psutil
import os

router = APIRouter(prefix="/system", tags=["System"])

@router.get("/status")
def system_info():
    """Returns global system metrics (CPU, RAM, Rock 5C specific configs)"""
    # Try to read temperature from thermal zone (Linux/Armbian)
    temp = None
    try:
        thermal_path = "/sys/class/thermal/thermal_zone0/temp"
        if os.path.exists(thermal_path):
            with open(thermal_path) as f:
                temp = round(int(f.read().strip()) / 1000.0, 1)
    except Exception:
        pass
    
    mem = psutil.virtual_memory()
    return {
        "platform": platform.system(),
        "arch": platform.machine(),
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": mem.percent,
        "memory_used_mb": round(mem.used / (1024 * 1024)),
        "memory_total_mb": round(mem.total / (1024 * 1024)),
        "temperature_c": temp,
        "uptime_s": round(psutil.boot_time()),
        "ip": _get_local_ip()
    }

@router.get("/version")
def get_version():
    """Returns FlashNode-AI version information"""
    return {
        "name": "FlashNode-AI",
        "version": "1.0.0",
        "platform": f"{platform.system()} {platform.machine()}",
        "python": platform.python_version()
    }

@router.get("/history")
def get_logs(limit: int = 100, offset: int = 0):
    """Returns operations history"""
    return history_db.get_history(limit, offset)


def _get_local_ip() -> str:
    """Attempts to determine the local IP address"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "unknown"
