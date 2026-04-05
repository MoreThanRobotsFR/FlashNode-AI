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
            # We can mock a continuous stream of system data here
            await websocket.send_json({
                "cpu": psutil.cpu_percent(),
                "ram_mb": psutil.virtual_memory().used / (1024 * 1024),
                "temp_c": 45  # Mocked
            })
            await asyncio.sleep(2)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel="system")


