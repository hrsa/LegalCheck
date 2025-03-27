from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from google.genai.live import AsyncSession

from app.api.v1.schemas.policy import PolicyInDB, PolicyCreate, PolicyUpdate, PolicyWithRules
from app.api.v1.services.policy_service import get_policies, get_policy, create_policy, update_policy, delete_policy, \
    get_active_policies_by_company
from app.db.session import get_async_session

router = APIRouter()


@router.get("/", response_model=list[PolicyInDB])
async def read_policies(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_async_session)):
    return await get_policies(db, skip=skip, limit=limit)

@router.get("/company/{company_id}", response_model=list[PolicyWithRules])
async def read_policies_by_company(company_id: int, db: AsyncSession = Depends(get_async_session)):
    return await get_active_policies_by_company(db, company_id=company_id)


@router.get("/{policy_id}", response_model=PolicyInDB)
async def read_policy(policy_id: int, db: AsyncSession = Depends(get_async_session)):
    policy = await get_policy(db, policy_id=policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.post("/", response_model=PolicyInDB)
async def create_policy_api(policy: PolicyCreate, db: AsyncSession = Depends(get_async_session)):
    return await create_policy(db, policy)


@router.put("/{policy_id}", response_model=PolicyInDB)
async def update_policy_api(policy_id: int, policy: PolicyUpdate, db: AsyncSession = Depends(get_async_session)):
    updated_policy = await update_policy(db, policy_data=policy)
    if updated_policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    return updated_policy


@router.delete("/{policy_id}/")
async def delete_policy_api(policy_id: int, db: AsyncSession = Depends(get_async_session)):
    result = await delete_policy(db, policy_id=policy_id)
    if not result:
        raise HTTPException(status_code=404, detail="Policy not found")
    return {"detail": f"Policy {policy_id} deleted successfully."}
