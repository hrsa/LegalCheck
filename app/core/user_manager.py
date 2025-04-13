from typing import Optional

from fastapi import Depends, Request, WebSocket
from fastapi_users import BaseUserManager, IntegerIDMixin, FastAPIUsers
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import auth_backend
from app.core.config import settings
from app.db.models import AccessToken
from app.db.models.user import User, get_user_db, get_access_token_db
from app.db.session import get_async_session


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend]
)

def get_current_user(
        active: bool = False,
        verified: bool = False,
        superuser: bool = False
):
    return fastapi_users.current_user(active=active, verified=verified, superuser=superuser)

async def get_websocket_user(
        websocket: WebSocket,
        db: AsyncSession,
        user_manager=Depends(get_user_manager),
) -> Optional[User]:
    token = None

    # Try to get token from query parameters first
    token_from_query = websocket.query_params.get("token")
    if token_from_query:
        token = token_from_query
        logger.info("Using token from query parameter")

    # If no token in query params, try to get it from cookies
    if not token:
        cookies = websocket.headers.get("cookie", "")
        if cookies:
            cookie_pairs = cookies.split("; ")
            for pair in cookie_pairs:
                if pair.startswith(f"legalcheck_access_token="):
                    token = pair.split("=", 1)[1]
                    logger.info("Using token from cookie")
                    break

    # If still no token, authentication fails
    if not token:
        logger.warning("No authentication token found in either query parameters or cookies")
        return None

    # Query the token from the database
    query = await db.execute(
        select(AccessToken).where(AccessToken.token == token)
    )
    access_token = query.scalar_one_or_none()
    if not access_token:
        return None

    # Get the user
    user = await db.execute(select(User).where(User.id == access_token.user_id))
    user = user.scalar_one_or_none()
    if user is None:
        return None

    return user

