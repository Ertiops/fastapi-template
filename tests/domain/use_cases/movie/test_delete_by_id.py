from collections.abc import Awaitable, Callable
from uuid import uuid7

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database.tables import MovieTable
from app.application.exceptions import (
    EntityNotFoundException,
)
from app.domain.use_cases.movie.delete_by_id import DeleteMovieByIdUC
from tests.utils.common import now_utc


async def test__delete_by_id(
    delete_movie_by_id_uc: DeleteMovieByIdUC,
    create_movie: Callable[..., Awaitable[MovieTable]],
    session: AsyncSession,
) -> None:
    db_movie = await create_movie()
    await delete_movie_by_id_uc.execute(input_dto=db_movie.id)
    await session.refresh(db_movie, attribute_names=["deleted_at"])
    assert db_movie.deleted_at is not None


async def test__delete_by_id__entity_not_found_exception(
    delete_movie_by_id_uc: DeleteMovieByIdUC,
) -> None:
    with pytest.raises(EntityNotFoundException):
        await delete_movie_by_id_uc.execute(input_dto=uuid7())


async def test__delete_by_id__entity_not_found_exception__deleted(
    delete_movie_by_id_uc: DeleteMovieByIdUC,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movie = await create_movie(deleted_at=now_utc())
    with pytest.raises(EntityNotFoundException):
        await delete_movie_by_id_uc.execute(input_dto=db_movie.id)
