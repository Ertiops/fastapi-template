from collections.abc import Awaitable, Callable
from uuid import UUID

import pytest

from app.adapters.database.tables import MovieTable
from app.domain.entities.common import ItemList
from app.domain.entities.movie import Movie, MovieListParams
from app.domain.use_cases.movie.get_list import GetMovieListUC


async def test__get_list(
    get_movie_list_uc: GetMovieListUC,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movies = [await create_movie(id=UUID(int=i + 1)) for i in range(3)]
    result = await get_movie_list_uc.execute(input_dto=MovieListParams(limit=10))
    assert result == ItemList(
        items=[
            Movie(
                id=db_movie.id,
                title=db_movie.title,
                description=db_movie.description,
                year=db_movie.year,
                director=db_movie.director,
                genre=db_movie.genre,
                duration_minutes=db_movie.duration_minutes,
                rating=db_movie.rating,
                created_at=db_movie.created_at,
                updated_at=db_movie.updated_at,
            )
            for db_movie in reversed(db_movies)
        ],
        next_cursor=None,
    )


@pytest.mark.parametrize(
    ("after", "expected_id", "expected_cursor"),
    [
        (None, UUID(int=3), UUID(int=3)),
        (UUID(int=3), UUID(int=2), UUID(int=2)),
        (UUID(int=2), UUID(int=1), None),
    ],
)
async def test__get_list__limit_and_cursor(
    get_movie_list_uc: GetMovieListUC,
    create_movie: Callable[..., Awaitable[MovieTable]],
    after: UUID | None,
    expected_id: UUID,
    expected_cursor: UUID | None,
) -> None:
    for value in (1, 2, 3):
        await create_movie(id=UUID(int=value))
    result = await get_movie_list_uc.execute(
        input_dto=MovieListParams(limit=1, after=after)
    )
    assert ([movie.id for movie in result.items], result.next_cursor) == (
        [expected_id],
        expected_cursor,
    )


async def test__get_list__exactly_full_last_page(
    get_movie_list_uc: GetMovieListUC,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movies = [await create_movie(id=UUID(int=i + 1)) for i in range(2)]
    result = await get_movie_list_uc.execute(input_dto=MovieListParams(limit=2))
    assert ([movie.id for movie in result.items], result.next_cursor) == (
        [movie.id for movie in reversed(db_movies)],
        None,
    )


async def test__get_list__empty_list(get_movie_list_uc: GetMovieListUC) -> None:
    result = await get_movie_list_uc.execute(input_dto=MovieListParams(limit=10))
    assert result == ItemList(items=[], next_cursor=None)


async def test__get_list__absent_anchor(
    get_movie_list_uc: GetMovieListUC,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    await create_movie(id=UUID(int=5))
    result = await get_movie_list_uc.execute(
        input_dto=MovieListParams(limit=10, after=UUID(int=8))
    )
    assert ([movie.id for movie in result.items], result.next_cursor) == (
        [UUID(int=5)],
        None,
    )
