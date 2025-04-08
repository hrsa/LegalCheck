from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel

from app.api.v1.schemas.rule import RuleInDB, RuleWithSimilarity


class PolicyType(str, Enum):
    company = "company"
    industry = "industry"
    standard = "standard"


class PolicyBase(BaseModel, from_attributes = True):
    name: str
    description: Optional[str] = None
    policy_type: PolicyType
    source_url: Optional[str] = None
    is_active: bool = True
    company_id: Optional[int] = None


class PolicyCreate(PolicyBase):
    pass


class PolicyUpdate(PolicyBase):
    name: Optional[str] = None
    policy_type: Optional[PolicyType] = None
    is_active: Optional[bool] = None


class PolicyInDB(PolicyBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

class PolicyWithRules(PolicyInDB):
    rules: List[RuleInDB]

class PolicyWithRulesForSemanticSearch(PolicyInDB):
    rules: Optional[List[RuleWithSimilarity]]
    similarity: float