from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ws.connection_manager import manager
import asyncio

router = APIRouter()

@router.websocket("/pipeline/status")
async def pipeline_status_ws(websocket: WebSocket):
    print(f"[WS] Accepting pipeline_status. Manager ID: {id(manager)}")
    await manager.connect(websocket, channel="pipeline_status")
    try:
        while True:
            # Keep-alive
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel="pipeline_status")
