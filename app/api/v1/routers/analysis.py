from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.analysis import AnalysisResult
from app.api.v1.services.analysis_service import analyze_document, upload_document_to_gemini, \
    chat_with_document
from app.db.session import get_async_session

router = APIRouter()


@router.post("/{document_id}/analyze", response_model=AnalysisResult)
async def analyze_uploaded_document(document_id: int, db: AsyncSession = Depends(get_async_session)):
    try:
        document = await upload_document_to_gemini(db, document_id)
        analysis_data = await analyze_document(db, document)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return analysis_data


@router.post("/{document_id}/chat")
async def chat_to_the_document(document_id: int, message: str = Form(...),
                               db: AsyncSession = Depends(get_async_session)):
    try:
        return await chat_with_document(db, document_id, message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

