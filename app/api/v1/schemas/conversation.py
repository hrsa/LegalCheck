from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel


class MessageAuthor(str, Enum):
    user = "User"
    legalcheck = "LegalCheck"


class MessageBase(BaseModel, from_attributes=True):
    content: str
    conversation_id: int
    author: MessageAuthor


class MessageCreate(MessageBase):
    pass


class MessageInDB(MessageBase):
    id: int
    created_at: datetime


class ConversationBase(BaseModel, from_attributes=True):
    document_id: int
    user_id: int
    title: Optional[str] = None


class ConversationCreate(ConversationBase):
    pass


class ConversationUpdate(ConversationBase):
    user_id: Optional[int] = None
    document_id: Optional[int] = None
    title: str


class ConversationInDB(ConversationBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class ConversationWithMessages(ConversationInDB):
    messages: List[MessageInDB] = []