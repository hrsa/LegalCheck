from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.checklist import ChecklistInDB, ChecklistCreate, ChecklistUpdate, ChecklistWithRules
from app.api.v1.services.checklist_service import get_all_checklists, get_checklist, create_checklist, update_checklist, \
    delete_checklist
from app.core.config import settings
from app.core.user_manager import get_current_user
from app.db.models import User
from app.db.session import get_async_session

router = APIRouter(prefix=f"{settings.API_V1_STR}/checklists", tags=["checklists"],
                   dependencies=[Depends(get_current_user())])


@router.get("/", response_model=list[ChecklistWithRules])
async def read_checklists(user: User = Depends(get_current_user()), db: AsyncSession = Depends(get_async_session)):
    return await get_all_checklists(db, user)


@router.get("/{checklist_id}", response_model=ChecklistInDB)
async def read_checklist(checklist_id: int, db: AsyncSession = Depends(get_async_session)):
    checklist = await get_checklist(db, checklist_id)
    if checklist is None:
        raise HTTPException(status_code=404, detail="Checklist not found")
    return checklist


@router.post("/", response_model=ChecklistInDB)
async def create_checklist_api(checklist: ChecklistCreate, user: User = Depends(get_current_user()),
                               db: AsyncSession = Depends(get_async_session)):
    try:
        return await create_checklist(db, user, checklist)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.patch("/{checklist_id}", response_model=ChecklistInDB)
async def update_checklist_api(checklist_id: int, checklist: ChecklistUpdate, user: User = Depends(get_current_user()),
                               db: AsyncSession = Depends(get_async_session)):
    try:
        return await update_checklist(db, user, checklist_id, checklist_data=checklist)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.delete("/{checklist_id}")
async def delete_checklist_api(checklist_id: int, user: User = Depends(get_current_user()),
                               db: AsyncSession = Depends(get_async_session)):
    try:
        await delete_checklist(db, user, checklist_id=checklist_id)
        return {"detail": f"Checklist {checklist_id} deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
