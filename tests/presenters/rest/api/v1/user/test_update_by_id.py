from collections.abc import Awaitable, Callable, Mapping
from http import HTTPStatus
from typing import Any
from uuid import UUID, uuid7

import pytest
from dirty_equals import IsStr
from httpx import AsyncClient

from app.adapters.database.tables import UserTable


def api_url(user_id: UUID = uuid7()) -> str:
    return f"/api/v1/users/{user_id}/"


@pytest.mark.parametrize(
    "body",
    (
        dict(username="t" * 2),
        dict(username="t" * 256),
        dict(email="t" * 256 + "est@test.com"),
    ),
)
async def test__update_by_id__unprocessable_entity(
    client: AsyncClient, body: Mapping[str, Any]
) -> None:
    response = await client.patch(api_url())
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test__update_by_id__unprocessable_entity__empty_payload(
    client: AsyncClient,
) -> None:
    response = await client.patch(api_url())
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test__update_by_id__not_found(client: AsyncClient) -> None:
    response = await client.patch(
        api_url(),
        json=dict(username="test_username"),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


async def test__update_by_id__ok__status(
    client: AsyncClient,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    db_user = await create_user()
    response = await client.patch(
        api_url(db_user.id),
        json=dict(username="test_username"),
    )
    assert response.status_code == HTTPStatus.OK


async def test__update_by_id__ok__format(
    client: AsyncClient,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    db_user = await create_user()
    body = dict(
        username="test_username",
        email="test@test.com",
    )
    response = await client.patch(
        api_url(db_user.id),
        json=body,
    )
    assert response.json() == dict(
        id=str(db_user.id),
        username=body.get("username"),
        email=body.get("email"),
        created_at=IsStr,
        updated_at=IsStr,
    )


@pytest.mark.parametrize(
    "body",
    (
        dict(username="test_username"),
        dict(email="test@test.com"),
    ),
)
async def test__update_by_id__conflict__duplicates(
    create_user: Callable[..., Awaitable[UserTable]],
    client: AsyncClient,
    body: Mapping[str, Any],
) -> None:
    await create_user(**body)
    db_user = await create_user()
    response = await client.patch(
        api_url(db_user.id),
        json=body,
    )
    assert response.status_code == HTTPStatus.CONFLICT
