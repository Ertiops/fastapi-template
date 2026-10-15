from app.application.use_case import IUseCase
from app.domain.entities.common import ItemList
from app.domain.entities.user import User, UserListParams
from app.domain.interfaces.storages.user import IUserStorage
from app.domain.uow import AbstractUow


class GetUserListUC(IUseCase[UserListParams, ItemList[User]]):
    _user_storage: IUserStorage
    _uow: AbstractUow

    def __init__(
        self,
        uow: AbstractUow,
        user_storage: IUserStorage,
    ) -> None:
        self._user_storage = user_storage
        self._uow = uow

    async def execute(self, *, input_dto: UserListParams) -> ItemList[User]:
        async with self._uow:
            return await self._user_storage.get_list(input_dto=input_dto)
