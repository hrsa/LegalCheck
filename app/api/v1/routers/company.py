from fastapi import APIRouter
from fastapi.params import Depends
from google.genai.live import AsyncSession

from app.api.v1.schemas.company import CompanyInDB, CompanyCreate, CompanyUpdate
from app.api.v1.services.company import get_all_companies, get_company, create_company, update_company, delete_company
from app.core.user_manager import get_current_user
from app.db.models import User
from app.db.session import get_async_session

router = APIRouter()


@router.get("/", response_model=list[CompanyInDB])
async def get_companies(user: User = Depends(get_current_user(superuser=True)),
                        db: AsyncSession = Depends(get_async_session)):
    return await get_all_companies(db)


@router.get("/me", response_model=CompanyInDB)
async def get_my_company(user: User = Depends(get_current_user()), db: AsyncSession = Depends(get_async_session)):
    return await get_company(db=db, company_id=user.company_id)


@router.post("/", response_model=CompanyInDB)
async def create_company_api(company: CompanyCreate, user: User = Depends(get_current_user(superuser=True)),
                             db: AsyncSession = Depends(get_async_session)):
    return await create_company(db, company_data=company)


@router.patch("/{company_id}", response_model=CompanyInDB)
async def update_company_api(company_id: int, company: CompanyUpdate,
                             user: User = Depends(get_current_user(superuser=True)),
                             db: AsyncSession = Depends(get_async_session)):
    return await update_company(db, company_id=company_id, company_data=company)


@router.delete("/{company_id}/")
async def delete_company_api(company_id: int, user: User = Depends(get_current_user(superuser=True)),
                             db: AsyncSession = Depends(get_async_session)):
    return await delete_company(db, company_id)
