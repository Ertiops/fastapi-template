from collections.abc import Awaitable, Callable
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


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
    all_ids: list[UUID] = []
    cursor: str | None = None
    for index in range(4):
        params = {"limit": 3}
        if cursor is not None:
            params["after"] = cursor
        result = await client.get(f"/api/v1/{resource}/", params=params)
        assert result.status_code == 200
        payload = result.json()
        assert set(payload) == {"items", "next_cursor"}
        page = [UUID(item["id"]) for item in payload["items"]]
        assert page == [UUID(int=12 - index * 3 - j) for j in range(3)]
        assert len(page) == 3
        all_ids.extend(page)
        cursor = payload["next_cursor"]
        if index < 3:
            assert cursor == str(page[-1])
        else:
            assert cursor is None
    assert len(set(all_ids)) == 12


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
    from datetime import UTC, datetime

    create: Callable[..., Awaitable] = request.getfixturevalue(factory_name)
    await create(id=UUID(int=9))
    await create(id=UUID(int=8), deleted_at=datetime.now(UTC))
    await create(id=UUID(int=7))
    result = await client.get(
        f"/api/v1/{resource}/",
        params={"limit": 10, "after": str(UUID(int=8))},
    )
    assert result.status_code == 200
    assert [item["id"] for item in result.json()["items"]] == [str(UUID(int=7))]
    assert result.json()["next_cursor"] is None


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
    assert first.status_code == 200
    assert [item["id"] for item in first.json()["items"]] == [str(UUID(int=20))]
    anchor = first.json()["next_cursor"]
    assert anchor == str(UUID(int=20))
    # Later inserted record above anchor does not appear; below anchor can.
    await create(id=UUID(int=30))
    await create(id=UUID(int=7))
    second = await client.get(
        f"/api/v1/{resource}/", params={"limit": 10, "after": anchor}
    )
    assert second.status_code == 200
    assert [item["id"] for item in second.json()["items"]] == [
        str(UUID(int=10)),
        str(UUID(int=7)),
        str(UUID(int=5)),
    ]
    assert second.json()["next_cursor"] is None


async def test_new_orm_defaults_are_stdlib_uuidv7(user_storage, movie_storage) -> None:
    from app.adapters.database.tables import MovieTable, UserTable
    from app.domain.entities.movie import CreateMovie, MovieGenre
    from app.domain.entities.user import CreateUser

    # Polyfactory generates its own UUIDv4, so exercise the actual INSERT
    # where SQLAlchemy's default UUIDv7 generator is applied.
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
    assert user.id.version == 7
    assert movie.id.version == 7
    for table in (UserTable, MovieTable):
        default = table.__table__.c.id.default.arg
        assert default.__module__ == "uuid"
        assert default(None).version == 7


@pytest.mark.parametrize("table", ["users", "movies"])
async def test_uuid_primary_key_supports_descending_query_plan(
    table: str, session: AsyncSession
) -> None:
    # EXPLAIN (not ANALYZE) is read-only; a tiny table may prefer a Seq Scan.
    result = await session.execute(
        text(
            f"EXPLAIN SELECT id FROM {table} "
            "WHERE deleted_at IS NULL ORDER BY id DESC LIMIT 4"
        )
    )
    plan = "\n".join(str(row[0]) for row in result)
    assert "Limit" in plan
    assert "OFFSET" not in plan.upper()
