from typing import Any

import pytest
from sqlalchemy import func, insert, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database.base import BaseTable
from app.adapters.database.storages.movie import MovieStorage
from app.adapters.database.storages.user import UserStorage
from app.adapters.database.tables import MovieTable, UserTable
from app.domain.entities.movie import CreateMovie, MovieGenre
from app.domain.entities.user import CreateUser


@pytest.mark.parametrize(
    ("table", "values"),
    [
        (
            UserTable,
            {"username": "tz-created-user", "email": "tz-created@example.com"},
        ),
        (
            MovieTable,
            {
                "title": "Timestamp Created Movie",
                "description": "Database timestamp defaults",
                "year": 2026,
                "director": "Test Director",
                "genre": MovieGenre.DRAMA,
                "duration_minutes": 90,
                "rating": 4.0,
            },
        ),
    ],
    ids=("user", "movie"),
)
async def test_timestamps_on_insert_follow_postgres_clock_in_non_utc_session(
    session: AsyncSession,
    table: type[BaseTable],
    values: dict[str, Any],
) -> None:
    await session.execute(text("SET LOCAL TIME ZONE 'Pacific/Auckland'"))
    db_now = await session.scalar(select(func.now()))
    stmt = (
        insert(table)
        .values(**values)
        .returning(table.created_at, table.updated_at, table.deleted_at)
    )
    row = (await session.execute(stmt)).one()
    assert (row.created_at, row.updated_at, row.deleted_at) == (
        db_now,
        db_now,
        None,
    )


@pytest.mark.parametrize(
    ("table", "values", "field_name", "replacement"),
    [
        (
            UserTable,
            {"username": "tz-original-user", "email": "tz-original@example.com"},
            "username",
            "tz-renamed-user",
        ),
        (
            MovieTable,
            {
                "title": "Timestamp Original Movie",
                "description": "Update checks",
                "year": 2026,
                "director": "Test Director",
                "genre": MovieGenre.DRAMA,
                "duration_minutes": 90,
                "rating": 4.0,
            },
            "title",
            "Timestamp Renamed Movie",
        ),
    ],
    ids=("user", "movie"),
)
async def test_timestamps_on_update_follow_postgres_clock_in_non_utc_session(
    session: AsyncSession,
    table: type[BaseTable],
    values: dict[str, Any],
    field_name: str,
    replacement: str,
) -> None:
    await session.execute(text("SET LOCAL TIME ZONE 'America/New_York'"))
    db_now = await session.scalar(select(func.now()))
    created = (
        await session.execute(
            insert(table).values(**values).returning(table.id, table.created_at)
        )
    ).one()
    stmt = (
        update(table)
        .where(table.id == created.id)
        .values(**{field_name: replacement})
        .returning(table.created_at, table.updated_at)
    )
    row = (await session.execute(stmt)).one()
    assert (row.created_at, row.updated_at) == (created.created_at, db_now)


@pytest.mark.parametrize(
    ("storage_name", "create_params"),
    [
        (
            "user_storage",
            CreateUser(username="tz-soft-delete-user", email="tz-delete@example.com"),
        ),
        (
            "movie_storage",
            CreateMovie(
                title="Timestamp Soft Delete Movie",
                description="Soft delete timestamp test",
                year=2026,
                director="Test Director",
                genre=MovieGenre.DRAMA,
                duration_minutes=90,
                rating=4.0,
            ),
        ),
    ],
    ids=("user", "movie"),
)
async def test_soft_delete_uses_postgres_clock_in_non_utc_session(
    session: AsyncSession,
    request: pytest.FixtureRequest,
    storage_name: str,
    create_params: CreateUser | CreateMovie,
) -> None:
    await session.execute(text("SET LOCAL TIME ZONE 'Asia/Tokyo'"))
    db_now = await session.scalar(select(func.now()))
    storage: UserStorage | MovieStorage = request.getfixturevalue(storage_name)
    created = await storage.create(input_dto=create_params)
    await storage.delete_by_id(input_dto=created.id)
    table = UserTable if storage_name == "user_storage" else MovieTable
    row = (
        await session.execute(
            select(table.created_at, table.updated_at, table.deleted_at).where(
                table.id == created.id
            )
        )
    ).one()
    assert (row.created_at, row.updated_at, row.deleted_at) == (
        db_now,
        db_now,
        db_now,
    )
