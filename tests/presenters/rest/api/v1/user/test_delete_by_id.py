from collections.abc import Awaitable, Callable
from http import HTTPStatus
from uuid import UUID, uuid7

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database.tables import UserTable
from tests.utils.common import now_utc


def api_url(user_id: UUID = uuid7()) -> str:
    return f"/api/v1/users/{user_id}/"


async def test_delete_by_id__no_content__status(
    create_user: Callable[..., Awaitable[UserTable]],
    client: AsyncClient,
) -> None:
    db_user = await create_user()
    response = await client.delete(api_url(db_user.id))
    assert response.status_code == HTTPStatus.NO_CONTENT


async def test_delete_by_id__validate_deleted_at(
    create_user: Callable[..., Awaitable[UserTable]],
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    db_user = await create_user()
    await client.delete(api_url(db_user.id))
    await session.refresh(db_user)
    assert db_user.deleted_at is not None


async def test__delete_by_id__not_found(client: AsyncClient) -> None:
    response = await client.delete(api_url())
    assert response.status_code == HTTPStatus.NOT_FOUND


async def test__delete_by_id__not_found__deleted(
    client: AsyncClient,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    db_user = await create_user(deleted_at=now_utc())
    await client.delete(api_url(db_user.id))
    response = await client.delete(api_url(db_user.id))
    assert response.status_code == HTTPStatus.NOT_FOUND
