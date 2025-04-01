from fastapi import Depends
from fastapi_users.authentication.strategy import AccessTokenDatabase, DatabaseStrategy

from app.db.models.user import AccessToken, get_access_token_db


def get_database_strategy(access_token_db: AccessTokenDatabase[AccessToken] = Depends(get_access_token_db)) -> DatabaseStrategy:
    return DatabaseStrategy(access_token_db, lifetime_seconds=3600)