import asyncio
from urllib.parse import urlparse

import pytest
from alembic import command
from alembic.config import Config
from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.core.config import settings
from app.db.models import Company
from app.db.session import get_async_session


@pytest.mark.order(1)
@pytest.mark.asyncio(loop_scope="session")
async def test_environment_setup(db_session):
    """
    Test that:
    1. We're in testing environment (settings.TESTING)
    2. Verify testing database and create it if needed
    3. Run Alembic migrations and make sure there are no errors
    """
    assert settings.TESTING, "Not in testing environment"

    db_url = settings.DATABASE_URL
    print(f"Testing database URL: {db_url}")

    parsed_url = urlparse(db_url.replace('postgresql+asyncpg://', 'postgresql://'))
    db_name = parsed_url.path.lstrip('/')

    await create_test_db_if_not_exists(db_url, db_name)

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, run_migrations_up)
    await loop.run_in_executor(None, run_migrations_down)
    await loop.run_in_executor(None, run_migrations_up)

    await create_initial_company(db_session)

    assert True


async def create_test_db_if_not_exists(db_url, db_name):
    postgres_url = db_url.replace(db_name, 'postgres')
    engine = create_async_engine(postgres_url)

    try:
        async with engine.connect() as conn:
            # Check if database exists
            result = await conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"))
            exists = result.scalar() == 1

            if not exists:
                print(f"Creating test database: {db_name}")
                await conn.execute(text("COMMIT"))
                await conn.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"Test database created: {db_name}")
            else:
                print(f"Test database already exists: {db_name}")
    finally:
        await engine.dispose()


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
        country="USA"
    )
    db.add(company)
    await db.commit()