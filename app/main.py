import sys

from fastapi.params import Depends
from loguru import logger

from app.api.v1.schemas.user import UserBase, UserCreate, UserUpdate

from app.core.user_manager import fastapi_users, get_current_user
import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routers.analysis import router as analysis_router
from app.api.v1.routers.conversation import router as conversation_router
from app.api.v1.routers.document import router as document_router
from app.api.v1.routers.policy import router as policy_router
from app.api.v1.routers.rule import router as rule_router
from app.api.v1.routers.company import router as company_router
from app.api.v1.routers.checklist import router as checklist_router
from app.api.v1.routers.websocket import router as websocket_router
from app.api.v1.routers.user import router as register_router
from app.core.auth import auth_backend
from app.core.config import settings

logger.remove()

logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{message}</cyan>",
    level=settings.LOG_LEVEL,
)

logger.add(
    settings.LOG_FILE_PATH,
    rotation="00:00",
    retention="60 days",
    compression="zip",
    level=settings.LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)

# sentry_sdk.init(
#     dsn=settings.SENTRY_DSN_URL,
#     send_default_pii=True,
#     traces_sample_rate=1.0,
#     _experiments={
#         "continuous_profiling_auto_start": True,
#     },
# )

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

app.include_router(websocket_router)
app.include_router(checklist_router)
app.include_router(company_router)
app.include_router(policy_router)
app.include_router(document_router)
app.include_router(analysis_router)
app.include_router(rule_router)
app.include_router(conversation_router)
app.include_router(register_router)
app.include_router(fastapi_users.get_auth_router(auth_backend), prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
# app.include_router(fastapi_users.get_register_router(user_schema=UserBase, user_create_schema=UserCreate),
#                    prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(fastapi_users.get_users_router(user_schema=UserBase, user_update_schema=UserUpdate),
                   prefix=f"{settings.API_V1_STR}/users", tags=["users"],
                   dependencies=[Depends(get_current_user(active=True))])
app.include_router(fastapi_users.get_verify_router(user_schema=UserBase), prefix=f"{settings.API_V1_STR}/auth",
                   tags=["auth"])
app.include_router(fastapi_users.get_reset_password_router(), prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])

analysis_results = {}


@app.get("/")
def read_root():
    return {"message": f"Welcome to LegalCheck API."}
