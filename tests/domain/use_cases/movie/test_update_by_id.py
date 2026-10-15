from collections.abc import Awaitable, Callable
from uuid import uuid7

import pytest
from dirty_equals import IsDatetime

from app.adapters.database.tables import MovieTable
from app.application.exceptions import (
    EntityAlreadyExistsException,
    EntityNotFoundException,
)
from app.domain.entities.movie import (
    Movie,
    MovieGenre,
    UpdateMovie,
)
from app.domain.use_cases.movie.update_by_id import UpdateMovieByIdUC
from tests.utils.common import now_utc


async def test__update_by_id(
    update_movie_by_id_uc: UpdateMovieByIdUC,
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
    movie = await update_movie_by_id_uc.execute(input_dto=update_data)
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
    update_movie_by_id_uc: UpdateMovieByIdUC,
) -> None:
    with pytest.raises(EntityNotFoundException):
        await update_movie_by_id_uc.execute(
            input_dto=UpdateMovie(
                id=uuid7(),
                title="test_title",
            )
        )


async def test__update_by_id__entity_not_found_exception__deleted(
    update_movie_by_id_uc: UpdateMovieByIdUC,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movie = await create_movie(deleted_at=now_utc())
    with pytest.raises(EntityNotFoundException):
        await update_movie_by_id_uc.execute(
            input_dto=UpdateMovie(id=db_movie.id, title="test_title")
        )


async def test__update_by_id__entity_already_exists_exception(
    update_movie_by_id_uc: UpdateMovieByIdUC,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movie = await create_movie()
    db_movie_to_update = await create_movie()
    with pytest.raises(EntityAlreadyExistsException):
        await update_movie_by_id_uc.execute(
            input_dto=UpdateMovie(
                id=db_movie_to_update.id,
                title=db_movie.title,
                year=db_movie.year,
                director=db_movie.director,
            )
        )
