from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

class AnalysisRequest(BaseModel):
    checklist_id: int | None = None

class Conflict(BaseModel):
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


class PaymentTerm(BaseModel):
    title: str
    due_date: str
    payment_method: Optional[str]
    amount_due: Optional[float]
    currency: Optional[str]
    penalties: Optional[str]
    discount: Optional[str]
    notes: Optional[str]


class AnalysisResult(BaseModel, from_attributes=True):
    document_id: int
    title: str
    checklist_id: Optional[int] = None
    company_name: str
    conflicts: List[Conflict]
    risks: List[Risk]
    missing_clauses: List[MissingClause]
    suggestions: List[Suggestion]
    payment_terms: List[PaymentTerm]


class AnalysisResultInDb(AnalysisResult):
    id: int
    document_id: int
    title: Optional[str] = None
    checklist_name: Optional[str] = None
    company_name: Optional[str] = None
    conflicts: Optional[List[Conflict]] = None
    risks: Optional[List[Risk]] = None
    missing_clauses: Optional[List[MissingClause]] = None
    suggestions: Optional[List[Suggestion]] = None
    payment_terms: Optional[List[PaymentTerm]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
