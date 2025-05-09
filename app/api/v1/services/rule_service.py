from fastapi import BackgroundTasks
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, String, func

from app.api.v1.schemas.policy import PolicyType
from app.api.v1.schemas.rule import RuleCreate, RuleUpdate
from app.api.v1.services.embedding_service import create_embedding, delete_embedding
from app.db.models import PolicyRule, User, Policy
from app.db.soft_delete import filtered_select


async def get_rules(db: AsyncSession, policy_id: int):
    result = await db.execute(
        filtered_select(PolicyRule).filter(PolicyRule.policy_id == policy_id)
    )
    return result.scalars().all()


async def get_rule(db: AsyncSession, rule_id: int):
    result = await db.execute(
        filtered_select(PolicyRule).filter(PolicyRule.id == rule_id)
    )
    return result.scalar_one_or_none()


async def find_rules(db: AsyncSession, user: User, query: str):
    company_id = user.company_id

    policy_query = filtered_select(Policy.id).filter(
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

    rule_query = filtered_select(PolicyRule).filter(
        PolicyRule.policy_id.in_(accessible_policy_ids),
        PolicyRule.description.ilike(search_query)
    )

    result = await db.execute(rule_query)
    return result.scalars().all()


async def create_rule(background_tasks: BackgroundTasks, db: AsyncSession, rule: RuleCreate):
    db_rule = PolicyRule(**rule.model_dump())
    db.add(db_rule)
    await db.commit()
    await db.refresh(db_rule)
    background_tasks.add_task(create_embedding, db, policy=None, rule=db_rule)
    return db_rule


async def update_rule(background_tasks: BackgroundTasks, db: AsyncSession, rule_id: int, rule_data: RuleUpdate):
    db_rule = await get_rule(db, rule_id)
    if not db_rule:
        return None

    update_data = rule_data.model_dump(exclude_unset=True, exclude_none=True)

    for field, value in update_data.items():
        setattr(db_rule, field, value)

    await db.commit()
    await db.refresh(db_rule)
    background_tasks.add_task(create_embedding, db, policy=None, rule=db_rule)
    return db_rule


async def delete_rule(db: AsyncSession, rule_id: int):
    db_rule = await get_rule(db, rule_id)
    if db_rule:
        await db_rule.soft_delete(db=db, cascade=True)
        await db.commit()
        await delete_embedding(db, "rule", rule_id)
        return True
    return False
