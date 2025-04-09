from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.future import select

from app.api.v1.schemas.company import CompanyCreate, CompanyUpdate
from app.api.v1.schemas.policy import PolicyCreate, PolicyUpdate, PolicyType
from app.db.models import Policy, User, Company


async def get_all_companies(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(Company).offset(skip).limit(limit)
    )
    return result.scalars().all()

async def get_company(db: AsyncSession, company_id: int):
    result = await db.execute(
        select(Company).filter(Company.id == company_id)
    )
    return result.scalar_one_or_none()


async def create_company(db: AsyncSession, company_data: CompanyCreate):
    db_company = Company(**company_data.model_dump())
    db.add(db_company)
    await db.commit()
    await db.refresh(db_company)
    return db_company

async def update_company(db: AsyncSession, company_id: int, company_data: CompanyUpdate):
    db_company = await get_company(db, company_id)
    if not db_company:
        return None

    update_data = company_data.model_dump(exclude_unset=True, exclude_none=True)

    for field, value in update_data.items():
        setattr(db_company, field, value)

    await db.commit()
    await db.refresh(db_company)
    return db_company

async def delete_company(db: AsyncSession, company_id: int):
    db_company = await get_company(db, company_id)
    if not db_company:
        return None
    await db.delete(db_company)
    await db.commit()