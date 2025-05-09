from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.v1.schemas.checklist import ChecklistCreate, ChecklistUpdate, ChecklistType, ChecklistWithRules, \
    ChecklistInDB
from app.api.v1.schemas.rule import RuleInDB
from app.db.models import User, Company, Checklist, PolicyRule
from app.db.soft_delete import filtered_select


async def get_all_checklists(db: AsyncSession, user: User):
    if user.is_superuser:
        query = filtered_select(Checklist).order_by(Checklist.id.desc())
    else:
        query = filtered_select(Checklist).filter(
            or_(user.company_id == Checklist.company_id, user.id == Checklist.user_id))
    result = await db.execute(query)
    checklists = result.scalars().all()

    all_rule_ids = set()
    for checklist in checklists:
        if checklist.ruleset:
            all_rule_ids.update(checklist.ruleset)

    rules_map = {}
    if all_rule_ids:
        rules_query = filtered_select(PolicyRule).where(PolicyRule.id.in_(list(all_rule_ids)))
        rules_result = await db.execute(rules_query)
        rules = rules_result.scalars().all()
        rules_map = {rule.id: RuleInDB.model_validate(rule) for rule in rules}

    enhanced_checklists = []
    for checklist in checklists:
        checklist_base = ChecklistInDB.model_validate(checklist)
        rules = []
        if checklist.ruleset:
            rules = [rules_map.get(rule_id) for rule_id in checklist.ruleset if rule_id in rules_map]

        checklist_with_rules = ChecklistWithRules(
            **checklist_base.model_dump(),
            rules=rules
        )

        enhanced_checklists.append(checklist_with_rules)

    return enhanced_checklists


async def get_checklist(db: AsyncSession, checklist_id: int):
    result = await db.execute(
        filtered_select(Checklist).filter(Checklist.id == checklist_id)
    )
    return result.scalar_one_or_none()


async def create_checklist(db: AsyncSession, user: User, checklist_data: ChecklistCreate):
    await check_missing_rules(db, checklist_data.ruleset)

    if checklist_data.type == ChecklistType.company:
        checklist_data.user_id = None
        if not checklist_data.company_id:
            checklist_data.company_id = user.company_id
    elif checklist_data.type == ChecklistType.user:
        checklist_data.company_id = None
        if not checklist_data.user_id:
            checklist_data.user_id = user.id

    if not user.is_superuser:
        if not checklist_data.type:
            raise HTTPException(400, "You must specify a type for the checklist")
        if checklist_data.company_id is not None and checklist_data.company_id != user.company_id:
            raise HTTPException(403, "You can only create checklists for your own company")
        if checklist_data.user_id is not None and checklist_data.user_id != user.id:
            raise HTTPException(403, "You can only create checklists for yourself")
    else:
        if not checklist_data.type and not checklist_data.company_id and not checklist_data.user_id:
            raise HTTPException(400, "You must specify a type, company or user for the checklist")
        if checklist_data.company_id is None and checklist_data.user_id is None:
            raise HTTPException(400, "You must specify either a company or user for the checklist")
        if checklist_data.company_id is not None and checklist_data.user_id is not None:
            raise HTTPException(400, "You can only specify either a company or user for the checklist")

    if checklist_data.user_id is not None:
        user = await db.get(User, checklist_data.user_id)
        if not user:
            raise HTTPException(404, "User not found")

    if checklist_data.company_id is not None:
        company = await db.get(Company, checklist_data.company_id)
        if not company:
            raise HTTPException(404, "Company not found")

    db_checklist = Checklist(
        company_id=checklist_data.company_id,
        user_id=checklist_data.user_id,
        name=checklist_data.name,
        ruleset=checklist_data.ruleset,
    )
    db.add(db_checklist)
    await db.commit()
    await db.refresh(db_checklist)
    return db_checklist


async def update_checklist(db: AsyncSession, user: User, checklist_id: int, checklist_data: ChecklistUpdate):
    db_checklist = await get_checklist(db, checklist_id)
    if not db_checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")
    if db_checklist.user_id != user.id and db_checklist.company_id != user.company_id and not user.is_superuser:
        raise HTTPException(status_code=403,
                            detail="You don't have permission to edit this checklist")
    if checklist_data.ruleset:
        await check_missing_rules(db, checklist_data.ruleset)

    update_data = checklist_data.model_dump(exclude_unset=True, exclude_none=True)

    for field, value in update_data.items():
        setattr(db_checklist, field, value)

    await db.commit()
    await db.refresh(db_checklist)
    return db_checklist


async def delete_checklist(db: AsyncSession, user: User, checklist_id: int):
    db_checklist = await get_checklist(db, checklist_id)
    if not db_checklist:
        raise Exception("Checklist not found")
    if db_checklist.user_id != user.id and db_checklist.company_id != user.company_id and not user.is_superuser:
        raise Exception("You don't have permission to delete this checklist")
    await db_checklist.soft_delete(db=db, cascade=True)
    await db.commit()


async def check_missing_rules(db: AsyncSession, ruleset: list[int]):
    rule_ids = set(ruleset)

    query = filtered_select(PolicyRule.id).where(PolicyRule.id.in_(rule_ids))
    result = await db.execute(query)
    existing_rule_ids = set(result.scalars().all())

    missing_rule_ids = rule_ids - existing_rule_ids
    if missing_rule_ids:
        raise Exception(f"Rules with IDs {list(missing_rule_ids)} don't exist")
