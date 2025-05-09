from fastapi import APIRouter, Depends, HTTPException, Form, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.analysis import AnalysisResult, AnalysisResultInDb, AnalysisRequest
from app.api.v1.schemas.conversation import ConversationWithMessages, MessageInDB
from app.api.v1.services.analysis_service import analyze_document, upload_document_to_gemini, \
    chat_with_document, get_document_analysis_results, \
    get_all_analysis_results
from app.api.v1.services.conversation_service import get_conversation
from app.core.config import settings
from app.core.user_manager import get_current_user
from app.db.models import User
from app.db.session import get_async_session

router = APIRouter(prefix=f"{settings.API_V1_STR}/documents", tags=["analysis"],
                   dependencies=[Depends(get_current_user())])


@router.get("/analysis_results", response_model=list[AnalysisResultInDb])
async def get_all_analysis_results_api(user: User = Depends(get_current_user()),
                                       db: AsyncSession = Depends(get_async_session)):
    return await get_all_analysis_results(db, user)


@router.get("/{document_id}/analysis_results", response_model=list[AnalysisResultInDb])
async def get_document_analysis_results_api(document_id: int, user: User = Depends(get_current_user()),
                                            db: AsyncSession = Depends(get_async_session)):
    try:
        return await get_document_analysis_results(db, user, document_id)
    except HTTPException as e:
        raise e


@router.post("/{document_id}/analyze", response_model=AnalysisResultInDb)
async def analyze_uploaded_document(document_id: int, request_data: AnalysisRequest,
                                    db: AsyncSession = Depends(get_async_session)):
    try:
        document = await upload_document_to_gemini(db, document_id)
        checklist_id = request_data.checklist_id or None
        analysis_data = await analyze_document(db, document, checklist_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return analysis_data


@router.post("/{document_id}/chat", response_model=MessageInDB)
async def chat_to_the_document(document_id: int, message: str = Form(...), user: User = Depends(get_current_user()),
                               db: AsyncSession = Depends(get_async_session)):
    try:
        return await chat_with_document(db, document_id, user, message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/chat", response_model=ConversationWithMessages)
async def get_document_conversation(document_id: int, user: User = Depends(get_current_user()),
                                    db: AsyncSession = Depends(get_async_session)):
    try:
        return await get_conversation(db, document_id=document_id, user_id=user.id)
    except HTTPException as e:
        raise e
