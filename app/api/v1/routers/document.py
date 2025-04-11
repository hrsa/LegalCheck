from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.document import DocumentInDB, DocumentCreate
from app.api.v1.services.document_service import save_document, get_document, get_all_documents, delete_document
from app.core.user_manager import get_current_user
from app.db.models import User
from app.db.session import get_async_session

router = APIRouter()


@router.post("/", response_model=DocumentInDB)
async def upload_document(background_tasks: BackgroundTasks, company_id: int = Form(None), file: UploadFile = File(...),
                          db: AsyncSession = Depends(get_async_session), user: User = Depends(get_current_user())):
    return await save_document(db, file, user, background_tasks, company_id)


@router.get("/", response_model=list[DocumentInDB])
async def read_documents(user: User = Depends(get_current_user()), db: AsyncSession = Depends(get_async_session)):
    return await get_all_documents(db, user)


@router.get("/{document_id}/", response_model=DocumentInDB)
async def read_document(document_id: int, db: AsyncSession = Depends(get_async_session)):
    document = await get_document(db, document_id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.delete("/{document_id}/")
async def remove_document(document_id: int, user: User = Depends(get_current_user()),
                          db: AsyncSession = Depends(get_async_session)):
    try:
        await delete_document(db, user, document_id)
        return {"detail": f"Document {document_id} deleted successfully."}
    except HTTPException as e:
        raise e
