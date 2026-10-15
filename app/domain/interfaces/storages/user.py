from typing import Protocol
from uuid import UUID

from app.domain.entities.common import ItemList
from app.domain.entities.user import (
    CreateUser,
    UpdateUser,
    User,
    UserListParams,
)


class IUserStorage(Protocol):
    async def create(self, *, input_dto: CreateUser) -> User:
        pass

    async def get_by_id(self, *, input_dto: UUID) -> User | None:
        pass

    async def get_list(self, *, input_dto: UserListParams) -> ItemList[User]:
        pass

    async def exists_by_id(self, *, input_dto: UUID) -> bool:
        pass

    async def update_by_id(self, *, input_dto: UpdateUser) -> User:
        pass

    async def delete_by_id(self, *, input_dto: UUID) -> None:
        pass
