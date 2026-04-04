from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .connection_manager import manager
import asyncio
import json

router = APIRouter()

@router.websocket("/flash/progress")
async def flash_progress_ws(websocket: WebSocket):
    await manager.connect(websocket, channel="flash_progress")
    try:
        while True:
            # Stay alive, client might send heartbeats
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel="flash_progress")

@router.websocket("/flash/output")
async def flash_output_ws(websocket: WebSocket):
    await manager.connect(websocket, channel="flash_output")
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel="flash_output")
