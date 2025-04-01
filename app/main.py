from app.api.v1.schemas.user import UserBase, UserCreate, UserUpdate
from app.core.user_manager import fastapi_users
import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routers.analysis import router as analysis_router
from app.api.v1.routers.document import router as document_router
from app.api.v1.routers.policy import router as policy_router
from app.api.v1.routers.rule import router as rule_router
from app.core.auth import auth_backend
from app.core.config import settings

sentry_sdk.init(
    dsn=settings.SENTRY_DSN_URL,
    send_default_pii=True,
    traces_sample_rate=1.0,
    _experiments={
        "continuous_profiling_auto_start": True,
    },
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(policy_router, prefix=f"{settings.API_V1_STR}/policies", tags=["policies"])
app.include_router(document_router, prefix=f"{settings.API_V1_STR}/documents", tags=["documents"])
app.include_router(analysis_router, prefix=f"{settings.API_V1_STR}/documents", tags=["analysis"])
app.include_router(rule_router, prefix=f"{settings.API_V1_STR}/rules", tags=["rules"])
app.include_router(fastapi_users.get_auth_router(auth_backend), prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(fastapi_users.get_register_router(user_schema=UserBase, user_create_schema=UserCreate), prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(fastapi_users.get_users_router(user_schema=UserBase, user_update_schema=UserUpdate), prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(fastapi_users.get_verify_router(user_schema=UserBase), prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(fastapi_users.get_reset_password_router(), prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])

analysis_results = {}


@app.get("/")
def read_root():
    return {"message": "Welcome to LegalCheck API"}
