from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database.tables import MovieTable, UserTable
from app.domain.entities.movie import CreateMovie, MovieGenre
from app.domain.entities.user import CreateUser


@pytest.mark.parametrize(
    ("resource", "factory_name"),
    [("users", "create_user"), ("movies", "create_movie")],
)
async def test_keyset_walk_twelve_records(
    resource: str,
    factory_name: str,
    request: pytest.FixtureRequest,
    client: AsyncClient,
) -> None:
    create: Callable[..., Awaitable] = request.getfixturevalue(factory_name)
    for i in range(12):
        await create(id=UUID(int=i + 1))

    observed: list[tuple[int, set[str], list[UUID], str | None]] = []
    cursor: str | None = None
    for _ in range(4):
        params: dict[str, str | int] = {"limit": 3}
        if cursor is not None:
            params["after"] = cursor
        response = await client.get(f"/api/v1/{resource}/", params=params)
        payload = response.json()
        observed.append(
            (
                response.status_code,
                set(payload),
                [UUID(item["id"]) for item in payload["items"]],
                payload["next_cursor"],
            )
        )
        cursor = payload["next_cursor"]

    expected = [
        (
            200,
            {"items", "next_cursor"},
            [UUID(int=12 - index * 3 - j) for j in range(3)],
            str(UUID(int=10 - index * 3)) if index < 3 else None,
        )
        for index in range(4)
    ]
    assert observed == expected


@pytest.mark.parametrize(
    ("resource", "factory_name"),
    [("users", "create_user"), ("movies", "create_movie")],
)
async def test_deleted_cursor_can_be_used_as_numeric_boundary(
    resource: str,
    factory_name: str,
    request: pytest.FixtureRequest,
    client: AsyncClient,
) -> None:
    create: Callable[..., Awaitable] = request.getfixturevalue(factory_name)
    await create(id=UUID(int=9))
    await create(id=UUID(int=8), deleted_at=datetime.now(UTC))
    await create(id=UUID(int=7))
    response = await client.get(
        f"/api/v1/{resource}/",
        params={"limit": 10, "after": str(UUID(int=8))},
    )
    payload = response.json()
    assert (
        response.status_code,
        [item["id"] for item in payload["items"]],
        payload["next_cursor"],
    ) == (200, [str(UUID(int=7))], None)


@pytest.mark.parametrize(
    ("resource", "factory_name"),
    [("users", "create_user"), ("movies", "create_movie")],
)
async def test_insertions_between_pages_do_not_replay_earlier_rows(
    resource: str,
    factory_name: str,
    request: pytest.FixtureRequest,
    client: AsyncClient,
) -> None:
    create: Callable[..., Awaitable] = request.getfixturevalue(factory_name)
    for value in (20, 10, 5):
        await create(id=UUID(int=value))

    first = await client.get(f"/api/v1/{resource}/", params={"limit": 1})
    first_page = first.json()
    cursor = first_page["next_cursor"]
    await create(id=UUID(int=30))
    await create(id=UUID(int=7))
    second = await client.get(
        f"/api/v1/{resource}/", params={"limit": 10, "after": cursor}
    )
    second_page = second.json()

    assert (
        first.status_code,
        [item["id"] for item in first_page["items"]],
        cursor,
        second.status_code,
        [item["id"] for item in second_page["items"]],
        second_page["next_cursor"],
    ) == (
        200,
        [str(UUID(int=20))],
        str(UUID(int=20)),
        200,
        [str(UUID(int=10)), str(UUID(int=7)), str(UUID(int=5))],
        None,
    )


async def test_new_orm_defaults_are_stdlib_uuidv7(user_storage, movie_storage) -> None:
    user = await user_storage.create(
        input_dto=CreateUser(username="uuid7-new-user", email="uuid7@example.invalid")
    )
    movie = await movie_storage.create(
        input_dto=CreateMovie(
            title="UUIDv7 Movie",
            description="UUIDv7 created by ORM",
            year=2020,
            director="Example Director",
            genre=MovieGenre.DRAMA,
            duration_minutes=90,
            rating=5.0,
        )
    )
    generators = [table.__table__.c.id.default.arg for table in (UserTable, MovieTable)]
    assert (
        user.id.version,
        movie.id.version,
        [(factory.__module__, factory(None).version) for factory in generators],
    ) == (
        7,
        7,
        [("uuid", 7), ("uuid", 7)],
    )


@pytest.mark.parametrize("table", ["users", "movies"])
async def test_uuid_primary_key_supports_descending_query_plan(
    table: str, session: AsyncSession
) -> None:
    result = await session.execute(
        text(
            f"EXPLAIN SELECT id FROM {table} "
            "WHERE deleted_at IS NULL ORDER BY id DESC LIMIT 4"
        )
    )
    plan = "\n".join(str(row[0]) for row in result)
    assert "Limit" in plan and "OFFSET" not in plan.upper()
