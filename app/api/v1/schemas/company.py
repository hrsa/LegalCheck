from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CompanyBase(BaseModel, from_attributes = True):
    name: str
    registration_number: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None


class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(CompanyBase):
    name: Optional[str] = None
    registration_number: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None


class CompanyInDB(CompanyBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None