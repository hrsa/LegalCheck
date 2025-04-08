from fastapi_users.schemas import BaseUser, BaseUserCreate, BaseUserUpdate


class UserBase(BaseUser[int], from_attributes = True):
    first_name: str
    last_name: str
    company_id: int


class UserCreate(BaseUserCreate):
    first_name: str
    last_name: str
    company_id: int
    pass


class UserRead(UserBase):
    id: int


class UserUpdate(BaseUserUpdate):
    first_name: str
    last_name: str
    company_id: int
    pass
