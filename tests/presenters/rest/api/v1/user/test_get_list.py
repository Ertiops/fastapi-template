from collections.abc import Awaitable, Callable
from http import HTTPStatus
from uuid import UUID, uuid7

import pytest
from dirty_equals import IsStr
from httpx import AsyncClient

from app.adapters.database.tables import UserTable

API_URL = "/api/v1/users/"


@pytest.mark.parametrize(
    "params",
    [
        {"limit": -1},
        {"limit": 0},
        {"limit": "a"},
        {"limit": 101},
        {"offset": 1},
        {"offset": "a"},
        {"after": "invalid"},
        {"unused": "true"},
    ],
)
async def test__get_list__unprocessable_entity(
    client: AsyncClient, params: dict
) -> None:
    result = await client.get(API_URL, params=params)
    assert result.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.parametrize("field", ["limit", "after"])
async def test__get_list__duplicate_query_key(client: AsyncClient, field: str) -> None:
    value = "10" if field == "limit" else str(uuid7())
    result = await client.get(API_URL, params=[(field, value), (field, value)])
    assert result.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test__get_list__ok__status(client: AsyncClient) -> None:
    result = await client.get(API_URL)
    assert result.status_code == HTTPStatus.OK
    assert result.json() == {"items": [], "next_cursor": None}


async def test_get_list__ok__format(
    create_user: Callable[..., Awaitable[UserTable]],
    client: AsyncClient,
) -> None:
    db_users = [await create_user(id=UUID(int=i + 1)) for i in range(2)]
    response = await client.get(API_URL)
    assert response.json() == {
        "items": [
            {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "created_at": IsStr,
                "updated_at": IsStr,
            }
            for user in reversed(db_users)
        ],
        "next_cursor": None,
    }


async def test_get_list__validate_limit(
    create_user: Callable[..., Awaitable[UserTable]],
    client: AsyncClient,
) -> None:
    db_users = [await create_user(id=UUID(int=i + 1)) for i in range(3)]
    result = await client.get(API_URL, params={"limit": 1})
    assert result.status_code == HTTPStatus.OK
    assert [item["id"] for item in result.json()["items"]] == [str(db_users[-1].id)]
    assert result.json()["next_cursor"] == str(db_users[-1].id)


async def test_get_list__validate_after(
    create_user: Callable[..., Awaitable[UserTable]],
    client: AsyncClient,
) -> None:
    db_users = [await create_user(id=UUID(int=i + 1)) for i in range(3)]
    result = await client.get(API_URL, params={"after": str(db_users[-1].id)})
    assert [item["id"] for item in result.json()["items"]] == [
        str(db_users[1].id),
        str(db_users[0].id),
    ]
    assert result.json()["next_cursor"] is None


async def test_get_list__last_full_page(
    create_user: Callable[..., Awaitable[UserTable]],
    client: AsyncClient,
) -> None:
    await create_user()
    await create_user()
    result = await client.get(API_URL, params={"limit": 2})
    assert len(result.json()["items"]) == 2
    assert result.json()["next_cursor"] is None


async def test_get_list__absent_anchor(
    create_user: Callable[..., Awaitable[UserTable]],
    client: AsyncClient,
) -> None:
    await create_user(id=UUID(int=7))
    result = await client.get(API_URL, params={"after": str(UUID(int=9))})
    assert result.status_code == HTTPStatus.OK
    assert [item["id"] for item in result.json()["items"]] == [str(UUID(int=7))]
