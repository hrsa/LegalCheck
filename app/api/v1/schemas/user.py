from typing import Optional

from fastapi_users.schemas import BaseUser, BaseUserCreate, BaseUserUpdate
from pydantic import EmailStr, BaseModel


class UserBase(BaseUser[int], from_attributes=True):
    first_name: str
    last_name: str
    company_id: Optional[int] = None


class UserRegister(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    password: str
    invite_code: str


class UserCreate(BaseUserCreate):
    first_name: str
    last_name: str
    company_id: int


class UserRead(UserBase):
    id: int


class UserUpdate(BaseUserUpdate):
    first_name: str
    last_name: str
    company_id: int
