from typing import List, Dict, Any

from fastapi import WebSocket
from loguru import logger


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.conversation_subscribers: Dict[int, List[int]] = {}

    async def connect(self, websocket: WebSocket, user_id: int, conversation_id: int):
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

        if conversation_id not in self.conversation_subscribers:
            self.conversation_subscribers[conversation_id] = []
        if user_id not in self.conversation_subscribers[conversation_id]:
            self.conversation_subscribers[conversation_id].append(user_id)

        logger.info(f"User {user_id} connected to conversation {conversation_id}")

    def disconnect(self, websocket: WebSocket, user_id: int, conversation_id: int):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)

            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        if (conversation_id in self.conversation_subscribers and
                user_id in self.conversation_subscribers[conversation_id] and
                user_id not in self.active_connections):
            self.conversation_subscribers[conversation_id].remove(user_id)

            if not self.conversation_subscribers[conversation_id]:
                del self.conversation_subscribers[conversation_id]

        logger.info(f"User {user_id} disconnected from conversation {conversation_id}")

    async def broadcast_to_conversation(self, conversation_id: int, message: Any):
        if conversation_id not in self.conversation_subscribers:
            return

        for user_id in self.conversation_subscribers[conversation_id]:
            await self.send_to_user(user_id, message)

    async def send_to_user(self, user_id: int, message: Any):
        if user_id not in self.active_connections:
            return

        disconnected_websockets = []

        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {str(e)}")
                disconnected_websockets.append(websocket)

        for websocket in disconnected_websockets:
            self.active_connections[user_id].remove(websocket)
