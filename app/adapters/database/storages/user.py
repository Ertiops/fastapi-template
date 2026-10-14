from collections.abc import Sequence
from typing import NoReturn
from uuid import UUID

from sqlalchemy import exists, func, insert, select, update
from sqlalchemy.exc import DBAPIError, IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database.converters.user import convert_user
from app.adapters.database.tables import UserTable
from app.application.exceptions import (
    EntityAlreadyExistsException,
    EntityNotFoundException,
    StorageException,
)
from app.domain.entities.user import (
    CreateUser,
    UpdateUser,
    User,
    UserListParams,
)
from app.domain.interfaces.storages.user import IUserStorage


class UserStorage(IUserStorage):
    def __init__(self, session: AsyncSession) -> None:
        self.__session = session

    async def create(self, *, input_dto: CreateUser) -> User:
        stmt = insert(UserTable).values(**input_dto.to_dict()).returning(UserTable)
        try:
            result = (await self.__session.scalars(stmt)).one()
        except IntegrityError as e:
            self.__raise_exception(e)
        return convert_user(result=result)

    async def get_by_id(self, *, input_dto: UUID) -> User | None:
        stmt = select(UserTable).where(
            UserTable.id == input_dto, UserTable.deleted_at.is_(None)
        )
        result = await self.__session.scalar(stmt)
        return convert_user(result=result) if result else None

    async def get_list(self, *, input_dto: UserListParams) -> Sequence[User]:
        stmt = select(UserTable).where(UserTable.deleted_at.is_(None))
        if input_dto.after is not None:
            stmt = stmt.where(UserTable.id < input_dto.after)
        stmt = stmt.order_by(UserTable.id.desc()).limit(input_dto.limit + 1)
        result = await self.__session.scalars(stmt)
        return [convert_user(result=r) for r in result]

    async def exists_by_id(self, *, input_dto: UUID) -> bool:
        stmt = select(
            exists().where(UserTable.id == input_dto, UserTable.deleted_at.is_(None))
        )
        return bool(await self.__session.scalar(stmt))

    async def update_by_id(self, *, input_dto: UpdateUser) -> User:
        stmt = (
            update(UserTable)
            .where(
                UserTable.id == input_dto.id,
                UserTable.deleted_at.is_(None),
            )
            .values(**input_dto.to_dict())
            .returning(UserTable)
        )
        try:
            result = (await self.__session.scalars(stmt)).one()
        except NoResultFound as e:
            raise EntityNotFoundException(entity=User, entity_id=input_dto.id) from e
        except IntegrityError as e:
            self.__raise_exception(e)
        return convert_user(result=result)

    async def delete_by_id(self, *, input_dto: UUID) -> None:
        stmt = (
            update(UserTable)
            .where(UserTable.id == input_dto)
            .values(deleted_at=func.now())
        )
        await self.__session.execute(stmt)

    def __raise_exception(self, e: DBAPIError) -> NoReturn:
        constraint = e.__cause__.__cause__.constraint_name  # type: ignore[union-attr]
        match constraint:
            case "uq__users__username":
                raise EntityAlreadyExistsException("Username already exists") from e
            case "uq__users__email":
                raise EntityAlreadyExistsException("Email already exists") from e
        raise StorageException(self.__class__.__name__) from e
