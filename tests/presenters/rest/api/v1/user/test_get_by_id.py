from collections.abc import Awaitable, Callable
from http import HTTPStatus
from uuid import UUID, uuid7

from dirty_equals import IsStr
from httpx import AsyncClient

from app.adapters.database.tables import UserTable


def api_url(user_id: UUID = uuid7()) -> str:
    return f"/api/v1/users/{user_id}/"


async def test__get_by_id__not_found__status(client: AsyncClient) -> None:
    response = await client.get(api_url())
    assert response.status_code == HTTPStatus.NOT_FOUND


async def test__get_by_id__ok__status(
    create_user: Callable[..., Awaitable[UserTable]],
    client: AsyncClient,
) -> None:
    db_user = await create_user()
    response = await client.get(api_url(db_user.id))
    assert response.status_code == HTTPStatus.OK


async def test__get_by_id__ok__format(
    create_user: Callable[..., Awaitable[UserTable]],
    client: AsyncClient,
) -> None:
    db_user = await create_user()
    response = await client.get(api_url(db_user.id))
    assert response.json() == dict(
        id=str(db_user.id),
        username=db_user.username,
        email=db_user.email,
        created_at=IsStr,
        updated_at=IsStr,
    )
