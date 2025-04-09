from typing import List, Optional

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

class PaymentTerm(BaseModel):
    title: str
    due_date: str
    payment_method: Optional[str]
    amount_due: Optional[float]
    currency: Optional[str]
    penalties: Optional[str]
    discount: Optional[str]
    notes: Optional[str]




class AnalysisResult(BaseModel):
    document_id: int
    title: str
    company_name: str
    conflicts: List[Conflict]
    risks: List[Risk]
    missing_clauses: List[MissingClause]
    suggestions: List[Suggestion]
    payment_terms: List[PaymentTerm]