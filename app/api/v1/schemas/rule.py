from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Set
from pydantic import BaseModel, Json, field_validator


class RuleType(str, Enum):
    conflict = "conflict"
    risk = "risk"
    requirement = "requirement"


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class RuleBase(BaseModel, from_attributes = True):
    policy_id: int
    rule_type: RuleType
    description: Optional[str] = None
    severity: Severity
    keywords: List[str] = list()

    @field_validator('keywords', mode='after')
    @classmethod
    def ensure_unique(cls, v: List[str]) -> list:
        return list(set(v))


class RuleCreate(RuleBase):
    pass


class RuleUpdate(RuleBase):
    policy_id: Optional[int] = None
    rule_type: Optional[RuleType] = None
    description: Optional[str] = None
    severity: Optional[Severity] = None
    keywords: Optional[List[str]] = list()


    @field_validator('keywords', mode='after')
    @classmethod
    def ensure_unique(cls, v: List[str] | None) -> list:
        if v is None:
            return list()

        return list(set(v))


class RuleInDB(RuleBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class RuleWithSimilarity(RuleInDB):
    similarity: float


