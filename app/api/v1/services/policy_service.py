from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.future import select

from app.api.v1.schemas.policy import PolicyCreate, PolicyUpdate, PolicyType, PolicyWithRules
from app.api.v1.schemas.rule import RuleInDB
from app.db.models import Policy, User
from app.db.soft_delete import filtered_select


async def get_policies(db: AsyncSession, skip: int = 0, limit: int = 10):
    result = await db.execute(
        filtered_select(Policy).offset(skip).limit(limit)
    )
    return result.scalars().all()


async def get_active_policies_by_company(db: AsyncSession, company_id: int):
    result = await db.execute(
        filtered_select(Policy).filter(
            Policy.is_active == True,
            or_(
                (Policy.policy_type == PolicyType.company) & (Policy.company_id == company_id),
                Policy.policy_type.in_([PolicyType.industry, PolicyType.standard])
            )
        ).order_by(Policy.id.desc())
        .options(joinedload(Policy.rules))
    )
    policies = result.unique().scalars().all()
    policies_and_rules = []
    for policy in policies:
        filtered_rules = [RuleInDB.model_validate(rule) for rule in policy.rules if rule.is_deleted is False]

        policy_with_filtered_rules = PolicyWithRules(
            id=policy.id,
            company_id=policy.company_id,
            is_active=policy.is_active,
            policy_type=policy.policy_type,
            name=policy.name,
            description=policy.description,
            rules=filtered_rules,
            created_at=policy.created_at,
            updated_at=policy.updated_at
        )
        policies_and_rules.append(policy_with_filtered_rules)

    return policies_and_rules

async def get_policy(db: AsyncSession, policy_id: int):
    result = await db.execute(
        filtered_select(Policy).filter(Policy.id == policy_id)
    )
    return result.scalar_one_or_none()


async def create_policy(db: AsyncSession, user: User, policy: PolicyCreate):
    db_policy = Policy(**policy.model_dump())
    if policy.policy_type == PolicyType.company:
        db_policy.company_id = user.company_id

    db.add(db_policy)
    await db.commit()
    await db.refresh(db_policy)
    return db_policy


async def update_policy(db: AsyncSession, policy_id: int, policy_data: PolicyUpdate):
    db_policy = await get_policy(db, policy_id)
    if not db_policy:
        raise HTTPException(HTTPStatus.NOT_FOUND, detail="Policy not found")
    update_data = policy_data.model_dump(exclude_unset=True, exclude_none=True)

    for field, value in update_data.items():
        setattr(db_policy, field, value)

    await db.commit()
    await db.refresh(db_policy)
    return db_policy


async def delete_policy(db: AsyncSession, policy_id: int):
    db_policy = await get_policy(db, policy_id)
    if not db_policy:
        raise HTTPException(HTTPStatus.NOT_FOUND, detail="Policy not found")
    await db_policy.soft_delete(db=db, cascade=True)
    await db.commit()
