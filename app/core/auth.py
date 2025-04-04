from fastapi_users.authentication import BearerTransport, JWTStrategy, AuthenticationBackend, CookieTransport

from app.core.config import settings

bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

cookie_transport = CookieTransport(cookie_name="legalcheck_access_token", cookie_max_age=settings.ACCESS_TOKEN_EXPIRE_SECONDS, cookie_secure=False, cookie_httponly=True, cookie_samesite="lax")

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=settings.SECRET_KEY, lifetime_seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)