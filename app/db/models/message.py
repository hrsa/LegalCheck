from datetime import datetime, timezone
from sqlalchemy import ForeignKey, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"))
    content: Mapped[str] = mapped_column(String, nullable=False)
    author: Mapped[str] = mapped_column(default='User')
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
