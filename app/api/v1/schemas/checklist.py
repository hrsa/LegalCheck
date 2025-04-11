from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, computed_field

from app.api.v1.schemas.rule import RuleInDB


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

class ChecklistWithRules(ChecklistInDB):
    rules: list[RuleInDB]

    @computed_field
    def type(self) -> ChecklistType:
        return ChecklistType.company if self.company_id else ChecklistType.user