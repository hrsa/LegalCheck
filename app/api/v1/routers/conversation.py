from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.conversation import ConversationWithMessages, ConversationUpdate
from app.api.v1.services.conversation_service import update_conversation
from app.core.config import settings
from app.core.user_manager import get_current_user
from app.db.models import User
from app.db.session import get_async_session

router = APIRouter(prefix=f"{settings.API_V1_STR}/conversations", tags=["conversations"],
                   dependencies=[Depends(get_current_user())])


@router.patch("/{conversation_id}", response_model=ConversationWithMessages)
async def update_conversation_data(conversation_data: ConversationUpdate, conversation_id: int, user: User = Depends(get_current_user()),
                                       db: AsyncSession = Depends(get_async_session)):
    return await update_conversation(db, user, conversation_id, conversation_data)