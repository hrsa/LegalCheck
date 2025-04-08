import asyncio
import os

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine

from app.core.config import settings
from app.db.session import async_session_maker
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def set_test_env():
    os.environ["ENV_FILE"] = ".env.test"


@pytest_asyncio.fixture()
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture()
async def engine():
    engine = create_async_engine(settings.DATABASE_URL)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture()
async def db_session(engine):
    async_session_maker_test = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session_maker_test() as session:
        try:
            yield session
        finally:
            await session.close()
    await engine.dispose()

