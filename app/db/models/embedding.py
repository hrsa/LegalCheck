import datetime

from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import Mapped
from sqlalchemy.testing.schema import mapped_column

from app.db.base_class import Base


class Embedding(Base):
    __tablename__ = "embeddings"

    id: Mapped[int] = mapped_column( primary_key=True, index=True)
    content_type: Mapped[str] = mapped_column(String, nullable=False)
    content_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    embedding: Mapped[Vector | None] = mapped_column(Vector(3072), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True),
                                                          default=lambda: datetime.datetime.now(datetime.timezone.utc)
                                                          )
    updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True),
                                                                 default=lambda: datetime.datetime.now(
                                                                     datetime.timezone.utc),
                                                                 onupdate=lambda: datetime.datetime.now(
                                                                     datetime.timezone.utc))

    __table_args__ = (
        UniqueConstraint('content_type', 'content_id', name='uq_content_type_id'),
    )
