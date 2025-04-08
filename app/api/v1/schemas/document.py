from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DocumentBase(BaseModel, from_attributes = True):
    filename: str
    content_type: str
    company_id: Optional[int] = None


class DocumentCreate(DocumentBase):
    file_content: bytes  # for initially uploading text content directly


class DocumentInDB(DocumentBase):
    id: int
    file_path: str
    is_processed: bool
    created_at: datetime