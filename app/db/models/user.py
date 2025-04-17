from fastapi import Depends
from fastapi_users.db import SQLAlchemyBaseUserTable
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from fastapi_users_db_sqlalchemy.access_token import SQLAlchemyBaseAccessTokenTableUUID, SQLAlchemyAccessTokenDatabase
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship, declared_attr

from app.db.base_class import Base, BaseSoftDelete
from app.db.session import get_async_session


class User(SQLAlchemyBaseUserTable[int], BaseSoftDelete):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str]
    last_name: Mapped[str]
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))

    company: Mapped["Company"] = relationship("Company", back_populates="users")
    conversations: Mapped[list["Conversation"]] = relationship("Conversation", back_populates="user", cascade="delete")
    checklists: Mapped[list["Checklist"]] = relationship("Checklist", back_populates="user", cascade="delete")


class AccessToken(SQLAlchemyBaseAccessTokenTableUUID, Base):
    __tablename__ = "accesstoken"

    @declared_attr
    def user_id(cls) -> Mapped[int]:
        return mapped_column(Integer, ForeignKey("user.id", ondelete="cascade"), nullable=False)


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


async def get_access_token_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyAccessTokenDatabase(session, AccessToken)
