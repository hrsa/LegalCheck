from enum import Enum
from typing import Optional, Any, List
from pydantic import BaseModel
from datetime import datetime, timezone

from app.api.v1.schemas.conversation import MessageInDB, ConversationWithMessages


class WebSocketMessageType(str, Enum):
    CONNECT = "connect"
    HISTORY = "history"
    NEW_MESSAGE = "new_message"
    MESSAGE_RECEIVED = "message_received"
    TYPING = "typing"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"


class WebSocketMessage(BaseModel):
    type: WebSocketMessageType
    conversation_id: int
    timestamp: datetime = datetime.now(timezone.utc)
    payload: Optional[Any] = None


class ChatHistoryResponse(WebSocketMessage):
    type: WebSocketMessageType = WebSocketMessageType.HISTORY
    payload: ConversationWithMessages


class NewMessageRequest(BaseModel):
    content: str


class NewMessageResponse(WebSocketMessage):
    type: WebSocketMessageType = WebSocketMessageType.NEW_MESSAGE
    payload: MessageInDB


class TypingIndicator(WebSocketMessage):
    type: WebSocketMessageType = WebSocketMessageType.TYPING
    payload: dict = {"is_typing": True}


class ErrorMessage(WebSocketMessage):
    type: WebSocketMessageType = WebSocketMessageType.ERROR
    payload: dict = {"message": "An error occurred"}