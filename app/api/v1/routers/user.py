from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.user import UserCreate, UserRegister, UserRead
from app.api.v1.services.user_service import create_user
from app.core.config import settings
from app.core.user_manager import get_user_manager
from app.db.session import get_async_session

router = APIRouter(prefix=f"{settings.API_V1_STR}/register", tags=["register"])


@router.post("/", response_model=UserRead)
async def register_user(user_data: UserRegister, db: AsyncSession = Depends(get_async_session), user_manager = Depends(get_user_manager)):
    try:
        return await create_user(user_data, db, user_manager)
    except HTTPException as e:
        raise e
