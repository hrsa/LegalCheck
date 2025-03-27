from fastapi import Depends
from fastapi_users import FastAPIUsers, BaseUserManager
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

from app.db.models.user import User
from app.db.session import get_db


async def get_user_db(session=Depends(get_db)):
    yield SQLAlchemyUserDatabase(session, User)


class UserManager(BaseUserManager[UserDB]):
    user_db_model = UserDB


async def get_user_manager(user_db):
    yield UserManager(user_db)

fastapi_users = FastAPIUsers[UserDB, int](
    get_user_manager,
    [UserDB],
    UserDB,
    int,
)