from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.future import select

from app.api.v1.schemas.policy import PolicyCreate, PolicyUpdate
from app.db.models import Policy


async def get_policies(db: AsyncSession, skip: int = 0, limit: int = 10):
    result = await db.execute(
        select(Policy).offset(skip).limit(limit)
    )
    return result.scalars().all()


async def get_active_policies_by_company(db: AsyncSession, company_id: int):
    result = await db.execute(
        select(Policy).filter(Policy.company_id == company_id, Policy.is_active == True).options(joinedload(Policy.rules))
    )
    return result.unique().scalars().all()

async def get_policy(db: AsyncSession, policy_id: int):
    result = await db.execute(
        select(Policy).filter(Policy.id == policy_id)
    )
    return result.scalar_one_or_none()


async def create_policy(db: AsyncSession, policy: PolicyCreate):
    db_policy = Policy(**policy.model_dump())
    db.add(db_policy)
    await db.commit()
    await db.refresh(db_policy)
    return db_policy


async def update_policy(db: AsyncSession, policy_data: PolicyUpdate):
    result = await db.execute(
        select(Policy).filter(Policy.id == policy_data.id)
    )
    db_policy = result.scalar_one_or_none()
    if not db_policy:
        return None

    for field, value in policy_data.model_dump().items():
        if hasattr(db_policy, field):
            setattr(db_policy, field, value)

    await db.commit()
    await db.refresh(db_policy)
    return db_policy


async def delete_policy(db: AsyncSession, policy_id: int):
    result = await db.execute(
        select(Policy).filter(Policy.id == policy_id)
    )
    db_policy = result.scalar_one_or_none()
    if db_policy:
        await db.delete(db_policy)
        await db.commit()
        return True
    return False
