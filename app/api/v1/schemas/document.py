from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class DocumentBase(BaseModel, from_attributes = True):
    filename: str
    content_type: str
    company_id: Optional[int] = None


class DocumentCreate(DocumentBase):
    file_content: bytes  # for initially uploading text content directly


class DocumentInDB(DocumentBase):
    id: int
    filename: str
    is_processed: bool
    created_at: datetime

    @field_validator('filename', mode='after')
    @classmethod
    def simplify_filename(cls, v: str) -> str:
        return v[37:]
