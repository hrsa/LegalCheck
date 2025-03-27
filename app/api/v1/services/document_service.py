import os
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models import Document
from app.api.v1.schemas.document import DocumentCreate
from app.core.config import settings

DOCUMENT_STORAGE = os.path.join(settings.BASE_DIR, "storage/documents")


async def save_document(db: AsyncSession, document: DocumentCreate):
    if not os.path.exists(DOCUMENT_STORAGE):
        os.makedirs(DOCUMENT_STORAGE)

    unique_filename = f"{uuid.uuid4()}_{document.filename}"
    file_path = os.path.join(DOCUMENT_STORAGE, unique_filename)

    with open(file_path, "wb") as f:
        f.write(document.file_content)

    db_document = Document(
        filename=unique_filename,
        content_type=document.content_type,
        file_path=file_path,
        company_id=document.company_id,
        is_processed=False,
    )

    db.add(db_document)
    await db.commit()
    await db.refresh(db_document)
    return db_document


async def get_document(db: AsyncSession, document_id: int):
    result = await db.execute(
        select(Document).filter(Document.id == document_id)
    )
    return result.scalar_one_or_none()