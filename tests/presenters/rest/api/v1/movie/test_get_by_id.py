from collections.abc import Awaitable, Callable
from http import HTTPStatus
from uuid import UUID, uuid7

from dirty_equals import IsStr
from httpx import AsyncClient

from app.adapters.database.tables import MovieTable


def api_url(movie_id: UUID = uuid7()) -> str:
    return f"/api/v1/movies/{movie_id}/"


async def test__get_by_id__not_found__status(client: AsyncClient) -> None:
    response = await client.get(api_url())
    assert response.status_code == HTTPStatus.NOT_FOUND


async def test__get_by_id__ok__status(
    create_movie: Callable[..., Awaitable[MovieTable]],
    client: AsyncClient,
) -> None:
    db_movie = await create_movie()
    response = await client.get(api_url(db_movie.id))
    assert response.status_code == HTTPStatus.OK


async def test__get_by_id__ok__format(
    create_movie: Callable[..., Awaitable[MovieTable]], client: AsyncClient
) -> None:
    db_movie = await create_movie()
    response = await client.get(api_url(db_movie.id))
    assert response.json() == dict(
        id=str(db_movie.id),
        title=db_movie.title,
        description=db_movie.description,
        year=db_movie.year,
        director=db_movie.director,
        genre=db_movie.genre,
        duration_minutes=db_movie.duration_minutes,
        rating=db_movie.rating,
        created_at=IsStr,
        updated_at=IsStr,
    )
