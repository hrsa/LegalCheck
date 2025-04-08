from typing import List, Optional, Dict
from pydantic import BaseModel


class Conflict(BaseModel, from_attributes = True):
    policy_name: str
    conflict_detail: str


class Risk(BaseModel):
    risk_type: str
    detail: str


class MissingClause(BaseModel):
    clause_name: str
    suggestion: str

class Suggestion(BaseModel):
    title: str
    details: str


class AnalysisResult(BaseModel):
    document_id: int
    company_name: str
    conflicts: List[Conflict]
    risks: List[Risk]
    missing_clauses: List[MissingClause]
    suggestions: List[Suggestion]