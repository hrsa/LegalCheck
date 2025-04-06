from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.api.v1.schemas.rule import RuleInDB, RuleCreate, RuleUpdate
from app.api.v1.services.rule_service import get_rules, get_rule, create_rule as create_rule_service, \
    update_rule as update_rule_service, delete_rule as delete_rule_service
from app.db.session import get_async_session

router = APIRouter()


@router.get("/policy/{policy_id}", response_model=list[RuleInDB])
async def read_rules(policy_id: int, db: AsyncSession = Depends(get_async_session)):
    return await get_rules(db, policy_id)


@router.get("/{rule_id}", response_model=RuleInDB)
async def read_rule(rule_id: int, db: AsyncSession = Depends(get_async_session)):
    rule = await get_rule(db, rule_id=rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.post("/", response_model=RuleInDB)
async def create_rule(rule: RuleCreate, db: AsyncSession = Depends(get_async_session)):
    return await create_rule_service(db, rule)


@router.patch("/{rule_id}", response_model=RuleInDB)
async def update_rule(rule_id: int, rule: RuleUpdate, db: AsyncSession = Depends(get_async_session)):
    updated_rule = await update_rule_service(db, rule_id, rule_data=rule)
    if updated_rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    return updated_rule


@router.delete("/{rule_id}/")
async def delete_rule(rule_id: int, db: AsyncSession = Depends(get_async_session)):
    result = await delete_rule_service(db, rule_id=rule_id)
    if not result:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"detail": f"Rule {rule_id} deleted successfully."}
