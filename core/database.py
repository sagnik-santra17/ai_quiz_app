import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase


from core.config import settings


logger = logging.getLogger(__name__)


logger.info("Initializing database...")

async_engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    echo=False  
)


AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    autoflush=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    logger.debug("Database: Opening a new database connection...")
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            logger.debug("Database: Closing database connection...")


class Base(DeclarativeBase):
    pass