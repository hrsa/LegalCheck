from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.v1.schemas.rule import RuleCreate, RuleUpdate
from app.db.models import PolicyRule


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


async def create_rule(db: AsyncSession, rule: RuleCreate):
    db_rule = PolicyRule(**rule.model_dump())
    db.add(db_rule)
    await db.commit()
    await db.refresh(db_rule)
    return db_rule


async def update_rule(db: AsyncSession, rule_id: int, rule_data: RuleUpdate):
    result = await db.execute(
        select(PolicyRule).filter(PolicyRule.id == rule_id)
    )
    db_rule = result.scalar_one_or_none()
    if not db_rule:
        return None

    for field, value in rule_data.model_dump().items():
        if hasattr(db_rule, field):
            setattr(db_rule, field, value)

    await db.commit()
    await db.refresh(db_rule)
    return db_rule


async def delete_rule(db: AsyncSession, rule_id: int):
    result = await db.execute(
        select(PolicyRule).filter(PolicyRule.id == rule_id)
    )
    db_rule = result.scalar_one_or_none()
    if db_rule:
        await db.delete(db_rule)
        await db.commit()
        return True
    return False
