from fastapi import APIRouter
from fastapi.params import Depends
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import WebSocket

from app.api.v1.services.websocket_service import handle_websocket_connection
from app.core.config import settings
from app.core.user_manager import get_current_user, get_websocket_user
from app.db.models import User
from app.db.session import get_async_session

router = APIRouter(prefix=f"{settings.API_V1_STR}/ws", tags=["websocket"])


@router.websocket("/conversations/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: int, db: AsyncSession = Depends(get_async_session)):
    user = await get_websocket_user(websocket, db)
    if not user:
        logger.error("Websocket connection failed, no user found")
        return
    await handle_websocket_connection(websocket, conversation_id, user.id, db)