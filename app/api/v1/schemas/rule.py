from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Set
from pydantic import BaseModel, Json


class RuleType(str, Enum):
    conflict = "conflict"
    risk = "risk"
    requirement = "requirement"

class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class RuleBase(BaseModel):
    policy_id: int
    rule_type: RuleType
    description: Optional[str] = None
    severity: Severity
    keywords: Set[str] = set()


class RuleCreate(RuleBase):
    pass


class RuleUpdate(RuleBase):
    pass


class RuleInDB(RuleBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

class RuleWithSimilarity(RuleInDB):
    similarity: float

    class Config:
        from_attributes = True