from collections.abc import Awaitable, Callable
from unittest.mock import patch
from uuid import UUID

import pytest
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database.converters.movie import convert_movie
from app.adapters.database.converters.user import convert_user
from app.adapters.database.pagination import fetch_uuid_page
from app.adapters.database.storages.movie import MovieStorage
from app.adapters.database.storages.user import UserStorage
from app.adapters.database.tables import MovieTable, UserTable
from app.domain.entities.movie import MovieListParams
from app.domain.entities.user import UserListParams


@pytest.mark.parametrize(
    ("factory_name", "storage_name", "params_type", "converter_path", "converter"),
    [
        (
            "create_user",
            "user_storage",
            UserListParams,
            "app.adapters.database.storages.user.convert_user",
            convert_user,
        ),
        (
            "create_movie",
            "movie_storage",
            MovieListParams,
            "app.adapters.database.storages.movie.convert_movie",
            convert_movie,
        ),
    ],
)
async def test_get_list_uses_one_query_and_converts_only_visible_rows(
    session: AsyncSession,
    request: pytest.FixtureRequest,
    factory_name: str,
    storage_name: str,
    params_type: type[UserListParams] | type[MovieListParams],
    converter_path: str,
    converter: Callable,
) -> None:
    create: Callable[..., Awaitable] = request.getfixturevalue(factory_name)
    storage: UserStorage | MovieStorage = request.getfixturevalue(storage_name)
    for value in (1, 2, 3):
        await create(id=UUID(int=value))

    statements: list[str] = []

    def capture(_connection, _cursor, statement, _parameters, _context, _executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    engine = session.bind
    event.listen(engine.sync_engine, "before_cursor_execute", capture)
    try:
        with patch(converter_path, wraps=converter) as spy:
            page = await storage.get_list(input_dto=params_type(limit=2))
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", capture)

    assert (
        len(statements),
        spy.call_count,
        [item.id for item in page.items],
        page.next_cursor,
    ) == (
        1,
        2,
        [UUID(int=3), UUID(int=2)],
        UUID(int=2),
    )


@pytest.mark.parametrize("limit", [0, -1])
async def test_invalid_page_limit_is_rejected(
    session: AsyncSession, limit: int
) -> None:
    with pytest.raises(ValueError, match="limit must be positive"):
        await fetch_uuid_page(
            session=session,
            statement=select(UserTable),
            id_column=UserTable.id,
            limit=limit,
            after=None,
        )


@pytest.mark.parametrize("table", [UserTable, MovieTable])
async def test_existing_ordering_is_replaced_by_uuid_descending(
    session: AsyncSession,
    request: pytest.FixtureRequest,
    table: type[UserTable] | type[MovieTable],
) -> None:
    create: Callable[..., Awaitable] = request.getfixturevalue(
        "create_user" if table is UserTable else "create_movie"
    )
    for value in (1, 2, 3):
        await create(id=UUID(int=value))
    rows, next_cursor = await fetch_uuid_page(
        session=session,
        statement=select(table).order_by(table.id.asc()),
        id_column=table.id,
        limit=2,
        after=None,
    )
    assert ([row.id for row in rows], next_cursor) == (
        [UUID(int=3), UUID(int=2)],
        UUID(int=2),
    )
