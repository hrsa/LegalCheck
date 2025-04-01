from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.document import DocumentInDB, DocumentCreate
from app.api.v1.services.document_service import save_document, get_document
from app.db.session import get_async_session

router = APIRouter()


@router.post("/", response_model=DocumentInDB)
async def upload_document(company_id: int = Form(...), file: UploadFile = File(...), db: AsyncSession = Depends(get_async_session)):
    file_content = await file.read()
    document_data = {
        "filename": file.filename,
        "content_type": file.content_type,
        "company_id": company_id,
        "file_content": file_content,
    }

    return await save_document(db, DocumentCreate(**document_data))


@router.get("/{document_id}/", response_model=DocumentInDB)
async def read_document(document_id: int, db: AsyncSession = Depends(get_async_session)):
    document = await get_document(db, document_id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document