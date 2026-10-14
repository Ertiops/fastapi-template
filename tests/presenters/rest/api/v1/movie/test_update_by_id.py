from collections.abc import Awaitable, Callable, Mapping
from http import HTTPStatus
from typing import Any
from uuid import UUID, uuid7

import pytest
from dirty_equals import IsStr
from httpx import AsyncClient

from app.adapters.database.tables import MovieTable
from app.domain.entities.movie import MovieGenre
from tests.utils.common import now_utc


def api_url(movie_id: UUID = uuid7()) -> str:
    return f"/api/v1/movies/{movie_id}/"


@pytest.mark.parametrize(
    "body",
    (
        dict(title="t" * 2),
        dict(title="t" * 256),
        dict(year=now_utc().year + 1),
        dict(director="t" * 2),
        dict(director="t" * 256),
        dict(genre="test_wrong_genre"),
        dict(rating=11),
    ),
)
async def test__update_by_id__unprocessable_entity(
    client: AsyncClient, body: Mapping[str, Any]
) -> None:
    response = await client.patch(api_url(), json=body)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test__update_by_id__unprocessable_entity__empty_payload(
    client: AsyncClient,
) -> None:
    response = await client.patch(api_url())
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test__update_by_id__not_found(client: AsyncClient) -> None:
    response = await client.patch(
        api_url(),
        json=dict(title="test_movie"),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


async def test__update_by_id__ok__status(
    client: AsyncClient,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movie = await create_movie()
    response = await client.patch(
        api_url(db_movie.id),
        json=dict(title="test_movie"),
    )
    assert response.status_code == HTTPStatus.OK


async def test__update_by_id__ok__format(
    client: AsyncClient,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movie = await create_movie()
    body = dict(
        title="test_title",
        description="test_description",
        year=now_utc().year,
        director="test_director",
        genre=MovieGenre.COMEDY,
        duration_minutes=100,
        rating=4.5,
    )
    response = await client.patch(api_url(db_movie.id), json=body)
    assert response.json() == dict(
        id=str(db_movie.id),
        title=body.get("title"),
        description=body.get("description"),
        year=body.get("year"),
        director=body.get("director"),
        genre=body.get("genre"),
        duration_minutes=body.get("duration_minutes"),
        rating=body.get("rating"),
        created_at=IsStr,
        updated_at=IsStr,
    )


async def test__update_by_id__conflict__duplicate(
    client: AsyncClient,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movie = await create_movie(year=now_utc().year)
    db_movie_to_update = await create_movie()
    response = await client.patch(
        api_url(db_movie_to_update.id),
        json=dict(
            title=db_movie.title,
            year=db_movie.year,
            director=db_movie.director,
        ),
    )
    assert response.status_code == HTTPStatus.CONFLICT
