from collections.abc import Awaitable, Callable
from uuid import uuid7

import pytest

from app.adapters.database.tables import MovieTable
from app.application.exceptions import (
    EntityNotFoundException,
)
from app.domain.entities.movie import (
    Movie,
)
from app.domain.use_cases.movie.get_by_id import GetMovieByIdUC
from tests.utils.common import now_utc


async def test__get_by_id(
    get_movie_by_id_uc: GetMovieByIdUC,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movie = await create_movie()
    movie = await get_movie_by_id_uc.execute(input_dto=db_movie.id)
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


async def test__get_by_id__entity_not_found_exception(
    get_movie_by_id_uc: GetMovieByIdUC,
) -> None:
    with pytest.raises(EntityNotFoundException):
        await get_movie_by_id_uc.execute(input_dto=uuid7())


async def test__get_by_id__entity_not_found_exception__deleted(
    get_movie_by_id_uc: GetMovieByIdUC,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movie = await create_movie(deleted_at=now_utc())
    with pytest.raises(EntityNotFoundException):
        await get_movie_by_id_uc.execute(input_dto=db_movie.id)
