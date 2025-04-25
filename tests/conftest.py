import asyncio
import os

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.config import settings
from app.db.models import Company
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def set_test_env():
    os.environ["ENV_FILE"] = ".env.test"


@pytest_asyncio.fixture(loop_scope="package")
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture(scope="module", loop_scope="package", autouse=True)
async def engine():
    engine = create_async_engine(settings.DATABASE_URL)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="module", loop_scope="package", autouse=True)
async def db_session(engine):
    async_session_maker_test = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session_maker_test() as session:
        try:
            yield session
        finally:
            await session.close()
    await engine.dispose()


@pytest_asyncio.fixture(scope="module", loop_scope="package", autouse=True)
async def fresh_db_session(db_session):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, run_migrations_down)
    await loop.run_in_executor(None, run_migrations_up)

    await create_initial_company(db_session)

    yield db_session


def run_migrations_up():
    print("Running Alembic migrations...")

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

    print("Alembic migrations completed successfully")


def run_migrations_down():
    print("Running Alembic migrations...")

    alembic_cfg = Config("alembic.ini")
    command.downgrade(alembic_cfg, "base")

    print("Alembic downgrade completed successfully")


async def create_initial_company(db: AsyncSession):
    company = Company(
        name="Client Company",
        registration_number="1234567890",
        address="123 Main Street, New York, NY 10001",
        country="USA",
        invite_code="invitation"
    )
    db.add(company)
    await db.commit()


async def new_user(async_client, email: str, password: str, first_name: str = 'Test', last_name: str = 'User',
                   invite_code: str = 'invitation'):
    return await async_client.post(
        f"{settings.API_V1_STR}/register/",
        json={
            "email": email,
            "password": password,
            "first_name": first_name,
            "last_name": last_name,
            "invite_code": invite_code
        }
    )


async def login(async_client, email: str, password: str):
    return await async_client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={
            "username": email,
            "password": password
        }
    )

async def logout(async_client):
    return await async_client.get(f"{settings.API_V1_STR}/auth/logout")
