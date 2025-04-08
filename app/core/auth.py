from fastapi import Depends
from fastapi_users.authentication import BearerTransport, AuthenticationBackend, CookieTransport
from fastapi_users.authentication.strategy import AccessTokenDatabase, DatabaseStrategy

from app.core.config import settings
from app.db.models import AccessToken
from app.db.models.user import get_access_token_db

bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

cookie_transport = CookieTransport(cookie_name="legalcheck_access_token", cookie_max_age=settings.ACCESS_TOKEN_EXPIRE_SECONDS, cookie_secure=False, cookie_httponly=True, cookie_samesite="lax")


def get_database_strategy(access_token_db: AccessTokenDatabase[AccessToken] = Depends(get_access_token_db)) -> DatabaseStrategy:
    return DatabaseStrategy(access_token_db, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name="db",
    transport=cookie_transport,
    get_strategy=get_database_strategy,
)