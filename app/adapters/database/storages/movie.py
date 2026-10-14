from collections.abc import Sequence
from typing import NoReturn
from uuid import UUID

from sqlalchemy import exists, func, insert, select, update
from sqlalchemy.exc import DBAPIError, IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database.converters.movie import convert_movie
from app.adapters.database.tables import MovieTable
from app.application.exceptions import (
    EntityAlreadyExistsException,
    EntityNotFoundException,
    StorageException,
)
from app.domain.entities.movie import (
    CreateMovie,
    Movie,
    MovieListParams,
    UpdateMovie,
)
from app.domain.interfaces.storages.movie import IMovieStorage


class MovieStorage(IMovieStorage):
    def __init__(self, session: AsyncSession) -> None:
        self.__session = session

    async def create(self, *, input_dto: CreateMovie) -> Movie:
        stmt = insert(MovieTable).values(**input_dto.to_dict()).returning(MovieTable)
        try:
            result = (await self.__session.scalars(stmt)).one()
        except IntegrityError as e:
            self.__raise_exception(e)
        return convert_movie(result=result)

    async def get_by_id(self, *, input_dto: UUID) -> Movie | None:
        stmt = select(MovieTable).where(
            MovieTable.id == input_dto,
            MovieTable.deleted_at.is_(None),
        )
        result = await self.__session.scalar(stmt)
        return convert_movie(result=result) if result else None

    async def get_list(self, *, input_dto: MovieListParams) -> Sequence[Movie]:
        stmt = select(MovieTable).where(MovieTable.deleted_at.is_(None))
        if input_dto.after is not None:
            stmt = stmt.where(MovieTable.id < input_dto.after)
        stmt = stmt.order_by(MovieTable.id.desc()).limit(input_dto.limit + 1)
        result = await self.__session.scalars(stmt)
        return [convert_movie(result=r) for r in result]

    async def exists_by_id(self, *, input_dto: UUID) -> bool:
        stmt = select(
            exists().where(MovieTable.id == input_dto, MovieTable.deleted_at.is_(None))
        )
        return bool(await self.__session.scalar(stmt))

    async def update_by_id(self, *, input_dto: UpdateMovie) -> Movie:
        stmt = (
            update(MovieTable)
            .where(
                MovieTable.id == input_dto.id,
                MovieTable.deleted_at.is_(None),
            )
            .values(**input_dto.to_dict())
            .returning(MovieTable)
        )
        try:
            result = (await self.__session.scalars(stmt)).one()
        except NoResultFound as e:
            raise EntityNotFoundException(entity=Movie, entity_id=input_dto.id) from e
        except IntegrityError as e:
            self.__raise_exception(e)
        return convert_movie(result=result)

    async def delete_by_id(self, *, input_dto: UUID) -> None:
        stmt = (
            update(MovieTable)
            .where(MovieTable.id == input_dto)
            .values(deleted_at=func.now())
        )
        await self.__session.execute(stmt)

    def __raise_exception(self, e: DBAPIError) -> NoReturn:
        constraint = e.__cause__.__cause__.constraint_name  # type: ignore[union-attr]
        match constraint:
            case "ix__movies__title_year_director":
                raise EntityAlreadyExistsException("Movie already exists") from e
        raise StorageException(self.__class__.__name__) from e
