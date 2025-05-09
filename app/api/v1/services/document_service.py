import os
import uuid
from http import HTTPStatus

from fastapi import BackgroundTasks, UploadFile, HTTPException
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.analysers.document_processor import DocumentProcessor
from app.api.v1.schemas.document import DocumentCreate
from app.core.config import settings
from app.db.models import Document, User
from app.db.soft_delete import filtered_select

DOCUMENT_STORAGE = os.path.join(settings.BASE_DIR, "storage/documents")


async def save_document(db: AsyncSession, file: UploadFile, user: User, background_tasks: BackgroundTasks,
                        company_id: int = None, ) -> Document:
    file_content = await file.read()
    document = DocumentCreate(
        filename=file.filename,
        content_type=file.content_type,
        company_id=user.company_id,
        file_content=file_content,
    )

    if user.is_superuser:
        document.company_id = company_id
    else:
        document.company_id = user.company_id

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
    background_tasks.add_task(ocr_document, db_document.id, db)
    return db_document


async def get_document(db: AsyncSession, document_id: int):
    result = await db.execute(
        filtered_select(Document).filter(Document.id == document_id)
    )
    return result.scalar_one_or_none()


async def get_all_documents(db: AsyncSession, user: User, skip: int = 0, limit: int = 100):
    if user.is_superuser:
        query = filtered_select(Document).offset(skip).limit(limit).order_by(Document.id.desc())
    else:
        query = filtered_select(Document).filter(Document.company_id == user.company_id).offset(skip).limit(limit).order_by(Document.id.desc())

    result = await db.execute(query)
    return result.scalars().all()


async def ocr_document(document_id: int, db: AsyncSession) -> None:
    try:
        document = await get_document(db, document_id)

        if not document:
            logger.error(f"Document {document.id} not found in DB during background processing")
            return

        document.text_content = DocumentProcessor().process_document(document.file_path)
        await db.commit()
    except ValueError as e:
        logger.error(f"Error processing document {document_id}. {e}")


async def delete_document(db: AsyncSession, user: User, document_id: int):
    document = await get_document(db, document_id)

    if not document:
        raise HTTPException(HTTPStatus.NOT_FOUND, "Document not found")

    if not user.is_superuser and document.company_id != user.company_id:
        raise HTTPException(HTTPStatus.UNAUTHORIZED, "You are not authorized to delete this document")

    if isinstance(document.file_path, str):
        try:
            os.remove(document.file_path)
        except FileNotFoundError:
            logger.warning(f"Document {document_id} file was missing during removal")

    await document.soft_delete(db=db, cascade=True)

    await db.commit()
