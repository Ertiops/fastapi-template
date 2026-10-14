from collections.abc import Awaitable, Callable
from uuid import UUID, uuid7

import pytest
from dirty_equals import IsDatetime, IsUUID

from app.adapters.database.storages.movie import MovieStorage
from app.adapters.database.tables import MovieTable
from app.application.exceptions import (
    EntityAlreadyExistsException,
    EntityNotFoundException,
)
from app.domain.entities.movie import (
    CreateMovie,
    Movie,
    MovieGenre,
    MovieListParams,
    UpdateMovie,
)
from tests.utils.common import now_utc


async def test__create(movie_storage: MovieStorage) -> None:
    create_data = CreateMovie(
        title="test_title",
        description="test_description",
        year=now_utc().year,
        director="test_author",
        genre=MovieGenre.COMEDY,
        duration_minutes=120,
        rating=4.5,
    )
    movie = await movie_storage.create(input_dto=create_data)
    assert movie == Movie(
        id=IsUUID,
        title=create_data.title,
        description=create_data.description,
        year=create_data.year,
        director=create_data.director,
        genre=create_data.genre,
        duration_minutes=create_data.duration_minutes,
        rating=create_data.rating,
        created_at=IsDatetime,
        updated_at=IsDatetime,
    )


async def test__create__entity_already_exists_exception(
    movie_storage: MovieStorage,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movie = await create_movie()
    with pytest.raises(EntityAlreadyExistsException):
        await movie_storage.create(
            input_dto=CreateMovie(
                title=db_movie.title,
                description="test_description",
                year=db_movie.year,
                director=db_movie.director,
                genre=MovieGenre.COMEDY,
                duration_minutes=120,
                rating=4.5,
            )
        )


async def test__get_by_id(
    movie_storage: MovieStorage,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movie = await create_movie()
    movie = await movie_storage.get_by_id(input_dto=db_movie.id)
    assert movie == Movie(
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


async def test__get_by_id__none(movie_storage: MovieStorage) -> None:
    assert await movie_storage.get_by_id(input_dto=uuid7()) is None


async def test__get_by_id__deleted(
    movie_storage: MovieStorage,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movie = await create_movie(deleted_at=now_utc())
    assert await movie_storage.get_by_id(input_dto=db_movie.id) is None


async def test__get_list(
    movie_storage: MovieStorage,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movies = [await create_movie(id=UUID(int=i + 1)) for i in range(3)]
    movies = await movie_storage.get_list(input_dto=MovieListParams(limit=2))
    # Storage fetches one extra row to detect whether another page exists.
    assert [x.id for x in movies] == [row.id for row in reversed(db_movies)]


async def test__get_list__after(
    movie_storage: MovieStorage,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movies = [await create_movie(id=UUID(int=i + 1)) for i in range(3)]
    movies = await movie_storage.get_list(
        input_dto=MovieListParams(limit=1, after=db_movies[-1].id)
    )
    assert [x.id for x in movies] == [db_movies[1].id, db_movies[0].id]


async def test__get_list__deleted(
    movie_storage: MovieStorage,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    await create_movie(id=UUID(int=3), deleted_at=now_utc())
    await create_movie(id=UUID(int=2))
    movies = await movie_storage.get_list(input_dto=MovieListParams(limit=10))
    assert [x.id for x in movies] == [UUID(int=2)]


async def test__get_list__empty_list(movie_storage: MovieStorage) -> None:
    movies = await movie_storage.get_list(input_dto=MovieListParams(limit=10))
    assert movies == []


async def test__exists_by_id(
    movie_storage: MovieStorage,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movie = await create_movie()
    assert await movie_storage.exists_by_id(input_dto=db_movie.id)


async def test__exists_by_id__false(movie_storage: MovieStorage) -> None:
    assert await movie_storage.exists_by_id(input_dto=uuid7()) is False


async def test__exists_by_id__deleted(
    movie_storage: MovieStorage,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movie = await create_movie(deleted_at=now_utc())
    assert await movie_storage.exists_by_id(input_dto=db_movie.id) is False


async def test__update_by_id(
    movie_storage: MovieStorage,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movie = await create_movie()
    update_data = UpdateMovie(
        id=db_movie.id,
        title="test_title",
        description="test_description",
        year=now_utc().year,
        director="test_director",
        genre=MovieGenre.COMEDY,
        duration_minutes=100,
        rating=4.5,
    )
    movie = await movie_storage.update_by_id(input_dto=update_data)
    assert movie == Movie(
        id=db_movie.id,
        title=update_data.title,
        description=update_data.description,
        year=update_data.year,
        director=update_data.director,
        genre=update_data.genre,
        duration_minutes=update_data.duration_minutes,
        rating=update_data.rating,
        created_at=db_movie.created_at,
        updated_at=IsDatetime,
    )


async def test__update_by_id__entity_not_found_exception(
    movie_storage: MovieStorage,
) -> None:
    with pytest.raises(EntityNotFoundException):
        await movie_storage.update_by_id(
            input_dto=UpdateMovie(id=uuid7(), title="test_title")
        )


async def test__update_by_id__entity_not_found_exception__deleted(
    movie_storage: MovieStorage,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movie = await create_movie(deleted_at=now_utc())
    with pytest.raises(EntityNotFoundException):
        await movie_storage.update_by_id(
            input_dto=UpdateMovie(id=db_movie.id, title="test_title")
        )


async def test__update_by_id__entity_already_exists_exception(
    movie_storage: MovieStorage,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movie = await create_movie()
    db_movie_to_update = await create_movie()
    with pytest.raises(EntityAlreadyExistsException):
        await movie_storage.update_by_id(
            input_dto=UpdateMovie(
                id=db_movie_to_update.id,
                title=db_movie.title,
                year=db_movie.year,
                director=db_movie.director,
            )
        )


async def test__delete_by_id(
    movie_storage: MovieStorage,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movie = await create_movie()
    await movie_storage.delete_by_id(input_dto=db_movie.id)
    assert db_movie.deleted_at is not None
