from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ws.connection_manager import manager
import asyncio
import psutil

router = APIRouter()

@router.websocket("/system")
async def system_ws(websocket: WebSocket):
    await manager.connect(websocket, channel="system")
    try:
        while True:
            # Read temperature from thermal zone if available
            temp = 45  # Default mock
            try:
                import os
                thermal_path = "/sys/class/thermal/thermal_zone0/temp"
                if os.path.exists(thermal_path):
                    with open(thermal_path) as f:
                        temp = round(int(f.read().strip()) / 1000.0, 1)
            except Exception:
                pass
            
            mem = psutil.virtual_memory()
            await websocket.send_json({
                "cpu": psutil.cpu_percent(),
                "ram_mb": round(mem.used / (1024 * 1024)),
                "ram_total_mb": round(mem.total / (1024 * 1024)),
                "temp_c": temp
            })
            await asyncio.sleep(2)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel="system")


@router.websocket("/system/logs")
async def system_logs_ws(websocket: WebSocket):
    """Live stream of backend FastAPI logs"""
    import logging
    
    await manager.connect(websocket, channel="system_logs")
    
    # Create a custom handler that sends logs to the WebSocket
    class WSLogHandler(logging.Handler):
        def __init__(self, ws: WebSocket):
            super().__init__()
            self.ws = ws
            self._loop = asyncio.get_event_loop()
        
        def emit(self, record):
            try:
                from datetime import datetime
                msg = {
                    "level": record.levelname,
                    "msg": self.format(record),
                    "logger": record.name,
                    "ts": datetime.fromtimestamp(record.created).isoformat()
                }
                asyncio.run_coroutine_threadsafe(
                    self.ws.send_json(msg), self._loop
                )
            except Exception:
                pass
    
    handler = WSLogHandler(websocket)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter('%(name)s - %(message)s'))
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    
    try:
        while True:
            # Keep-alive, client may send heartbeats
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        root_logger.removeHandler(handler)
        manager.disconnect(websocket, channel="system_logs")
