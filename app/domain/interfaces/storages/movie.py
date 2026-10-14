from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from app.domain.entities.movie import (
    CreateMovie,
    Movie,
    MovieListParams,
    UpdateMovie,
)


class IMovieStorage(Protocol):
    async def create(self, *, input_dto: CreateMovie) -> Movie:
        pass

    async def get_by_id(self, *, input_dto: UUID) -> Movie | None:
        pass

    async def get_list(self, *, input_dto: MovieListParams) -> Sequence[Movie]:
        pass

    async def exists_by_id(self, *, input_dto: UUID) -> bool:
        pass

    async def update_by_id(self, *, input_dto: UpdateMovie) -> Movie:
        pass

    async def delete_by_id(self, *, input_dto: UUID) -> None:
        pass
