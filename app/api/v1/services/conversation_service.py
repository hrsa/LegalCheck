from fastapi import HTTPException
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.v1.schemas.conversation import ConversationCreate, MessageAuthor, ConversationWithMessages, \
    ConversationUpdate
from app.db.models import Conversation, Message, User


async def get_conversation(db: AsyncSession, conversation_id: int = None, user_id: int = None, document_id: int = None):
    if not conversation_id and not (user_id and document_id):
        raise HTTPException(status_code=400,
                            detail="Either conversation_id or user_id and document_id must be provided")

    filters = []
    if conversation_id:
        filters.append(Conversation.id == conversation_id)
    if user_id and document_id:
        filters.append(Conversation.user_id == user_id)
        filters.append(Conversation.document_id == document_id)

    query = select(Conversation).filter(*filters).options(joinedload(Conversation.messages))

    result = await db.execute(query)
    conversation = result.unique().scalar_one_or_none()

    if conversation and conversation.is_deleted:
        await conversation.restore(db=db, restore_children=False)

    if not conversation and user_id and document_id:
        db_conversation = await create_conversation(db, ConversationCreate(document_id=document_id, user_id=user_id))
        return ConversationWithMessages(
            id=db_conversation.id,
            user_id=db_conversation.user_id,
            title=db_conversation.title,
            document_id=db_conversation.document_id,
            created_at=db_conversation.created_at,
            updated_at=db_conversation.updated_at,
            messages=[])

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ConversationWithMessages.model_validate(conversation, from_attributes=True)


async def create_conversation(db: AsyncSession, conversation_data: ConversationCreate):
    db_conversation = Conversation(**conversation_data.model_dump())
    db.add(db_conversation)
    await db.commit()
    await db.refresh(db_conversation)
    return db_conversation

async def update_conversation(db: AsyncSession, user: User, conversation_id: int, conversation_data: ConversationUpdate):
    result = await db.execute(select(Conversation).filter(Conversation.id == conversation_id))
    db_conversation = result.scalar_one_or_none()
    if not db_conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    update_data = conversation_data.model_dump(exclude_unset=True, exclude_none=True)

    db_conversation.title = update_data.get("title", db_conversation.title)

    if user.is_superuser:
        db_conversation.document_id = update_data.get("document_id", db_conversation.document_id)
        db_conversation.user_id = update_data.get("user_id", db_conversation.user_id)

    await db.commit()
    return await get_conversation(db, conversation_id)


async def add_message(db: AsyncSession, conversation_id: int, message: str, author: MessageAuthor):
    conversation = await get_conversation(db, conversation_id)
    if not conversation:
        raise ValueError("Conversation not found")

    message = Message(conversation_id=conversation_id, content=message, author=author)
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def get_recent_messages(db: AsyncSession, conversation_id: int, message_count: int = 4):
    conversation = await get_conversation(db, conversation_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    query = (select(Message).filter(Message.conversation_id == conversation_id)
             .order_by(Message.created_at.desc())
             .offset(1)
             .limit(message_count))
    result = await db.execute(query)
    return result.scalars().all()
