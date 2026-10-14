from httpx import ASGITransport, AsyncClient
import pytest_asyncio
import pytest

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator

from core.config import settings
from core.database import Base, get_db
from models.session import Session
from models.question import Question
from models.attempt import Attempt
from main import app




# Test async engine
test_async_engine: AsyncEngine = create_async_engine(
    settings.TEST_DATABASE_URL,
)

# Test async session maker
TestAsyncSessionLocal = async_sessionmaker(
    bind=test_async_engine,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession
)


# Shared session-wide database schema setup
@pytest_asyncio.fixture(scope="session", autouse=True)
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


# Automatically flushes the Redis cache before every single test execution
@pytest_asyncio.fixture(autouse=True, scope="function")
async def clear_redis():
    from core.redis import redis_client
    await redis_client.flushdb()
    yield