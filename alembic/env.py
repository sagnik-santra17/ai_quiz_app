import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# 1. Imported your application configuration settings object
from core.config import settings  
from core.database import Base
from models.session import Session
from models.question import Question
from models.attempt import Attempt

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    # 2. ALSO inject your settings URL here so offline mode (generating SQL scripts) works seamlessly
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # 3. Pull the dictionary section configuration from ini
    section = config.get_section(config.config_ini_section, {})
    
    # 4. OVERWRITE the placeholder string with your dynamic secure application database URL
    section["sqlalchemy.url"] = settings.DATABASE_URL

    connectable = async_engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # 5. Clean up the inline loop management to follow the async template's expected block
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    # 6. Fallback safety structure checking for pre-existing running loops
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # If an event loop is already open (e.g. testing setups), nest it cleanly
        loop.create_task(run_async_migrations())
    else:
        run_migrations_online()
