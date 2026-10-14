from collections.abc import Awaitable, Callable
from uuid import UUID

from app.adapters.database.tables import MovieTable
from app.domain.entities.common import ItemList
from app.domain.entities.movie import MovieListParams
from app.domain.use_cases.movie.get_list import GetMovieListUC


async def test__get_list(
    get_movie_list_uc: GetMovieListUC,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movies = [await create_movie(id=UUID(int=i + 1)) for i in range(3)]
    result = await get_movie_list_uc.execute(input_dto=MovieListParams(limit=10))
    assert isinstance(result, ItemList)
    assert [movie.id for movie in result.items] == [
        row.id for row in reversed(db_movies)
    ]
    assert result.next_cursor is None


async def test__get_list__limit_and_cursor(
    get_movie_list_uc: GetMovieListUC,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movies = [await create_movie(id=UUID(int=i + 1)) for i in range(3)]
    first = await get_movie_list_uc.execute(input_dto=MovieListParams(limit=1))
    assert [movie.id for movie in first.items] == [db_movies[-1].id]
    assert first.next_cursor == db_movies[-1].id
    second = await get_movie_list_uc.execute(
        input_dto=MovieListParams(limit=1, after=first.next_cursor)
    )
    assert [movie.id for movie in second.items] == [db_movies[-2].id]
    assert second.next_cursor == db_movies[-2].id
    last = await get_movie_list_uc.execute(
        input_dto=MovieListParams(limit=1, after=second.next_cursor)
    )
    assert [movie.id for movie in last.items] == [db_movies[0].id]
    assert last.next_cursor is None


async def test__get_list__exactly_full_last_page(
    get_movie_list_uc: GetMovieListUC,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    await create_movie()
    await create_movie()
    result = await get_movie_list_uc.execute(input_dto=MovieListParams(limit=2))
    assert len(result.items) == 2
    assert result.next_cursor is None


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
    assert [movie.id for movie in result.items] == [UUID(int=5)]
    assert result.next_cursor is None
