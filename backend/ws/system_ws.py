from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .connection_manager import manager
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

@router.websocket("/pipeline/status")
async def pipeline_ws(websocket: WebSocket):
    await manager.connect(websocket, channel="pipeline")
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel="pipeline")
