from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class ChecklistType(str, Enum):
    company = "company"
    user = "user"

class ChecklistBase(BaseModel, from_attributes = True):
    name: str

class ChecklistCreate(ChecklistBase):
    user_id: Optional[int] = None
    type: Optional[ChecklistType] = None
    company_id: Optional[int] = None
    ruleset: list[int]


class ChecklistUpdate(ChecklistBase):
    name: Optional[str] = None
    ruleset: Optional[list[int]] = None


class ChecklistInDB(ChecklistBase):
    id: int
    user_id: Optional[int] = None
    company_id: Optional[int] = None
    ruleset: list[int]
    created_at: datetime
    updated_at: Optional[datetime] = None