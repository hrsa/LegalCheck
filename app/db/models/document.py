from datetime import datetime, timezone

from sqlalchemy import Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column, CascadeOptions

from app.db.base_class import BaseSoftDelete


class Document(BaseSoftDelete):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String)
    content_type: Mapped[str] = mapped_column(String)
    file_path: Mapped[str] = mapped_column(String)
    text_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    company_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("companies.id"), nullable=True)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                          default=lambda: datetime.now(timezone.utc)
                                                          )
    gemini_name: Mapped[str | None] = mapped_column(String, nullable=True)

    company: Mapped["Company"] = relationship("Company", back_populates="documents")
    analysis_results: Mapped[list["AnalysisResult"]] = relationship("AnalysisResult", back_populates="document", cascade="delete")
    conversations: Mapped[list["Conversation"]] = relationship("Conversation", back_populates="document", cascade="delete")
    embedding: Mapped["Embedding"] = relationship("Embedding",
                             primaryjoin="and_(foreign(Embedding.content_id)==Document.id, Embedding.content_type=='document')",
                             uselist=False, viewonly=True)
    linked_documents: Mapped[list["LinkedDocument"]] = relationship("LinkedDocument", back_populates="parent_document")
