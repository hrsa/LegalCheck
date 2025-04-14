from http import HTTPStatus

from fastapi import HTTPException
from fastapi_users import exceptions
from fastapi_users.router import ErrorCode
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status

from app.api.v1.schemas.user import UserCreate, UserRegister
from app.core.user_manager import get_user_manager
from app.db.models import Company, User


async def create_user(user_data: UserRegister, db: AsyncSession, user_manager):
    result = await db.execute(select(Company).filter(Company.invite_code == user_data.invite_code))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(HTTPStatus.FORBIDDEN, detail="Invalid invite code")

    try:
        user_dict = user_data.model_dump(exclude={"invite_code"})
        user_dict["company_id"] = company.id
        new_user_data = UserCreate.model_validate(user_dict)

        created_user = await user_manager.create(user_create=new_user_data, safe=True)
        return created_user
    except exceptions.UserAlreadyExists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.REGISTER_USER_ALREADY_EXISTS,
        )
    except exceptions.InvalidPasswordException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": ErrorCode.REGISTER_INVALID_PASSWORD,
                "reason": e.reason,
            },
        )
