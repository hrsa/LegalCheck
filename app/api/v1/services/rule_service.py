from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, String, func

from app.api.v1.schemas.policy import PolicyType
from app.api.v1.schemas.rule import RuleCreate, RuleUpdate
from app.db.models import PolicyRule, User, Policy


async def get_rules(db: AsyncSession, policy_id: int):
    result = await db.execute(
        select(PolicyRule).filter(PolicyRule.policy_id == policy_id)
    )
    return result.scalars().all()


async def get_rule(db: AsyncSession, rule_id: int):
    result = await db.execute(
        select(PolicyRule).filter(PolicyRule.id == rule_id)
    )
    return result.scalar_one_or_none()


async def find_rules(db: AsyncSession, user: User, query: str):
    company_id = user.company_id

    policy_query = select(Policy.id).filter(
        Policy.is_active == True,
        or_(
            (Policy.policy_type == PolicyType.company) & (Policy.company_id == company_id),
            Policy.policy_type.in_([PolicyType.industry, PolicyType.standard])
        )
    )
    policy_result = await db.execute(policy_query)
    accessible_policy_ids = policy_result.scalars().all()

    if not accessible_policy_ids:
        return []

    search_query = f"%{query}%"

    rule_query = select(PolicyRule).filter(
        PolicyRule.policy_id.in_(accessible_policy_ids),
        PolicyRule.description.ilike(search_query)
    )

    result = await db.execute(rule_query)
    return result.scalars().all()


async def create_rule(db: AsyncSession, rule: RuleCreate):
    db_rule = PolicyRule(**rule.model_dump())
    db.add(db_rule)
    await db.commit()
    await db.refresh(db_rule)
    return db_rule


async def update_rule(db: AsyncSession, rule_id: int, rule_data: RuleUpdate):
    db_rule = await get_rule(db, rule_id)
    if not db_rule:
        return None

    update_data = rule_data.model_dump(exclude_unset=True, exclude_none=True)

    for field, value in update_data.items():
        setattr(db_rule, field, value)

    await db.commit()
    await db.refresh(db_rule)
    return db_rule


async def delete_rule(db: AsyncSession, rule_id: int):
    db_rule = await get_rule(db, rule_id)
    if db_rule:
        await db.delete(db_rule)
        await db.commit()
        return True
    return False
