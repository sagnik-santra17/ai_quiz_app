# Disable the background worker during tests so it doesn't touch the real database.
import os
os.environ["WORKER_ENABLED"] = "False"

import pytest_asyncio
import pytest

from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock
from sqlalchemy.pool import NullPool

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator

from core.config import settings
from core.database import Base, get_db
from models.session import Session
from models.question import Question
from models.attempt import Attempt
from main import app
import core.redis



# Test async engine
test_async_engine: AsyncEngine = create_async_engine(
    settings.TEST_DATABASE_URL,
    poolclass=NullPool
)


# Test async session maker
TestAsyncSessionLocal = async_sessionmaker(
    bind=test_async_engine,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession
)


# Shared session-wide database schema setup
@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database():
    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# # Throws a new DB session per test — rolled back at teardown so tests stay isolated
@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_async_engine.connect() as connection:
        async with connection.begin() as transaction:
            async_session = AsyncSession(
                bind=connection,
                expire_on_commit=False,
                join_transaction_mode="create_savepoint",
            )
            try:
                yield async_session
            finally:
                await async_session.close()
                await transaction.rollback()


# HTTP AsyncClient fixture - sends the actual requests: GET/POST/PUT/DELETE
@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    async def _get_get_db():
        yield db_session
    app.dependency_overrides[get_db] = _get_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


"""# Automatically flushes the Redis cache before every single test execution
@pytest_asyncio.fixture(autouse=True, scope="function")
async def clear_redis():
    yield"""


# Mock Redis
@pytest.fixture(autouse=True)
def mock_redis_middleware():
    """
    Automatically mocks the global redis_client to prevent loop mismatches.
    """
    # Keep a reference to the original client to restore it later
    original_client = core.redis.redis_client
    
    # Instantiate an asynchronous mock object
    mock_client = AsyncMock()
    
    # Configure the 'incr' command to always return a low request count
    mock_client.incr.return_value = 1
    
    # Dynamically hot-swap the real client with our mock
    core.redis.redis_client = mock_client
    
    yield mock_client
    
    # Restore the original configuration after the test finishes
    core.redis.redis_client = original_client