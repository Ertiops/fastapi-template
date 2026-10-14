from collections.abc import Awaitable, Callable
from http import HTTPStatus
from uuid import UUID, uuid7

import pytest
from dirty_equals import IsStr
from httpx import AsyncClient

from app.adapters.database.tables import MovieTable

API_URL = "/api/v1/movies/"


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
    response = await client.get(API_URL, params=params)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.parametrize("field", ["limit", "after"])
async def test__get_list__duplicate_query_key(client: AsyncClient, field: str) -> None:
    value = "10" if field == "limit" else str(uuid7())
    response = await client.get(API_URL, params=[(field, value), (field, value)])
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test__get_list__ok__status(client: AsyncClient) -> None:
    response = await client.get(API_URL)
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"items": [], "next_cursor": None}


async def test__get_list__ok__format(
    client: AsyncClient,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movies = [await create_movie(id=UUID(int=i + 1)) for i in range(2)]
    response = await client.get(API_URL)
    assert response.json() == {
        "items": [
            {
                "id": str(movie.id),
                "title": movie.title,
                "description": movie.description,
                "year": movie.year,
                "director": movie.director,
                "genre": movie.genre,
                "duration_minutes": movie.duration_minutes,
                "rating": movie.rating,
                "created_at": IsStr,
                "updated_at": IsStr,
            }
            for movie in reversed(db_movies)
        ],
        "next_cursor": None,
    }


async def test__get_list__validate_limit(
    client: AsyncClient,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movies = [await create_movie(id=UUID(int=i + 1)) for i in range(3)]
    response = await client.get(API_URL, params={"limit": 1})
    assert response.status_code == HTTPStatus.OK
    assert [item["id"] for item in response.json()["items"]] == [str(db_movies[-1].id)]
    assert response.json()["next_cursor"] == str(db_movies[-1].id)


async def test__get_list__validate_after(
    client: AsyncClient,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movies = [await create_movie(id=UUID(int=i + 1)) for i in range(3)]
    response = await client.get(API_URL, params={"after": str(db_movies[-1].id)})
    assert [item["id"] for item in response.json()["items"]] == [
        str(db_movies[1].id),
        str(db_movies[0].id),
    ]
    assert response.json()["next_cursor"] is None


async def test__get_list__last_full_page(
    client: AsyncClient,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    await create_movie()
    await create_movie()
    response = await client.get(API_URL, params={"limit": 2})
    assert len(response.json()["items"]) == 2
    assert response.json()["next_cursor"] is None


async def test__get_list__absent_anchor(
    client: AsyncClient,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    await create_movie(id=UUID(int=7))
    response = await client.get(API_URL, params={"after": str(UUID(int=9))})
    assert response.status_code == HTTPStatus.OK
    assert [item["id"] for item in response.json()["items"]] == [str(UUID(int=7))]
