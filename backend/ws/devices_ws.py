from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
from ws.connection_manager import manager

router = APIRouter()

@router.websocket("/devices")
async def devices_ws(websocket: WebSocket):
    await manager.connect(websocket, channel="devices")
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel="devices")

@router.websocket("/gpio")
async def gpio_ws(websocket: WebSocket):
    await manager.connect(websocket, channel="gpio")
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel="gpio")
