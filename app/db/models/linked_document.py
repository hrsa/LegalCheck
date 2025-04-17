import datetime

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship

from app.db.base_class import BaseSoftDelete


class LinkedDocument(BaseSoftDelete):
    __tablename__ = "linked_documents"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("documents.id"))
    url = Column(String)
    content = Column(Text, nullable=True)
    is_processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.UTC))

    parent_document = relationship("Document", back_populates="linked_documents")
