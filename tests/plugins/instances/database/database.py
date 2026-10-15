import asyncio
from collections.abc import AsyncIterator
from os import environ
from types import SimpleNamespace

import pytest
from alembic.config import Config as AlembicConfig
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.adapters.database.config import DatabaseConfig
from app.adapters.database.tables import BaseTable
from app.adapters.database.utils import (
    create_engine,
    create_sessionmaker,
    make_alembic_config,
)
from tests.utils.db import truncate_tables
from tests.utils.worker import get_worker_schema_name


@pytest.fixture(scope="session", autouse=True)
def event_loop():
    """Share one event loop across session-scoped async database fixtures."""
    loop = asyncio.new_event_loop()
    try:
        yield loop
    finally:
        loop.close()


@pytest.fixture(scope="session")
def db_config() -> DatabaseConfig:
    return DatabaseConfig(
        dsn=environ.get(
            "APP_DB_DSN",
            "postgresql+asyncpg://app:app@127.0.0.1:5432/app",
        ),
    )


@pytest.fixture(scope="session")
def alembic_config(db_config: DatabaseConfig) -> AlembicConfig:
    cmd_options = SimpleNamespace(
        config="alembic.ini",
        name="alembic",
        raiseerr=False,
        x=None,
    )
    return make_alembic_config(cmd_options, pg_url=db_config.dsn)


@pytest.fixture(scope="session")
async def engine_context(
    db_config: DatabaseConfig,
) -> None:
    schema = get_worker_schema_name()
    admin_engine = create_async_engine(db_config.dsn, future=True)
    async with admin_engine.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
        await conn.commit()
    await admin_engine.dispose()


@pytest.fixture(scope="session")
async def engine(
    db_config: DatabaseConfig,
    engine_context: None,
) -> AsyncIterator[AsyncEngine]:
    schema = get_worker_schema_name()
    async with create_engine(
        dsn=db_config.dsn,
        future=True,
        debug=False,
        connect_args={"server_settings": {"search_path": schema}},
    ) as engine:
        async with engine.begin() as connection:
            await connection.run_sync(BaseTable.metadata.create_all)
        await truncate_tables(engine, schema_name=schema)
        yield engine


@pytest.fixture(scope="session")
async def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return create_sessionmaker(engine=engine)


@pytest.fixture
async def session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session
        await session.rollback()
