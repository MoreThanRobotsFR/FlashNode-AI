from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
from ws.connection_manager import manager

router = APIRouter()

@router.websocket("/serial/{port_name}")
async def serial_ws(websocket: WebSocket, port_name: str):
    channel_name = f"serial_{port_name}"
    await manager.connect(websocket, channel=channel_name)
    try:
        while True:
            data = await websocket.receive_text()
            # In a real implementation we would write this data to the serial port
            # For now we just echo it or log it
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel=channel_name)
