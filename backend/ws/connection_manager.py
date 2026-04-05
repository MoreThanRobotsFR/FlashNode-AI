from fastapi import WebSocket
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Allow multiple typed channels
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str = "general"):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = []
        self.active_connections[channel].append(websocket)

    def disconnect(self, websocket: WebSocket, channel: str = "general"):
        if channel in self.active_connections:
            self.active_connections[channel].remove(websocket)

    async def broadcast(self, message: dict, channel: str = "general"):
        logger.info(f"[MANAGER] Broadcasting to {channel}. Active channels: {list(self.active_connections.keys())}")
        if channel in self.active_connections:
            logger.info(f"[MANAGER] Found {len(self.active_connections[channel])} clients in {channel}")
            for connection in self.active_connections[channel]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"[MANAGER] send error: {e}")
                    # Handle disconnected clients that didn't clean up correctly
                    pass

manager = ConnectionManager()
