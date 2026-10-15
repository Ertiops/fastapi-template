from collections.abc import Awaitable, Callable
from http import HTTPStatus
from uuid import UUID, uuid7

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database.tables import MovieTable
from tests.utils.common import now_utc


def api_url(movie_id: UUID = uuid7()) -> str:
    return f"/api/v1/movies/{movie_id}/"


async def test__delete_by_id__no_content__status(
    create_movie: Callable[..., Awaitable[MovieTable]],
    client: AsyncClient,
) -> None:
    db_movie = await create_movie()
    response = await client.delete(api_url(db_movie.id))
    assert response.status_code == HTTPStatus.NO_CONTENT


async def test__delete_by_id__validate_deleted_at(
    create_movie: Callable[..., Awaitable[MovieTable]],
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    db_movie = await create_movie()
    await client.delete(api_url(db_movie.id))
    await session.refresh(db_movie)
    assert db_movie.deleted_at is not None


async def test__delete_by_id__not_found(client: AsyncClient) -> None:
    response = await client.delete(api_url())
    assert response.status_code == HTTPStatus.NOT_FOUND


async def test__delete_by_id__not_found__deleted(
    create_movie: Callable[..., Awaitable[MovieTable]],
    client: AsyncClient,
) -> None:
    db_movie = await create_movie(deleted_at=now_utc())
    response = await client.delete(api_url(db_movie.id))
    assert response.status_code == HTTPStatus.NOT_FOUND
