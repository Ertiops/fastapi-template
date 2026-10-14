from collections.abc import Awaitable, Callable
from uuid import UUID, uuid7

import pytest
from dirty_equals import IsDatetime, IsUUID

from app.adapters.database.storages.user import UserStorage
from app.adapters.database.tables import UserTable
from app.application.exceptions import (
    EntityAlreadyExistsException,
    EntityNotFoundException,
)
from app.domain.entities.user import (
    CreateUser,
    UpdateUser,
    User,
    UserListParams,
)
from tests.utils.common import now_utc


async def test__create(
    user_storage: UserStorage,
) -> None:
    create_data = CreateUser(
        username="test_username",
        email="test@test.com",
    )
    user = await user_storage.create(input_dto=create_data)
    assert user == User(
        id=IsUUID,
        username=create_data.username,
        email=create_data.email,
        created_at=IsDatetime,
        updated_at=IsDatetime,
    )


async def test__create__entity_already_exists_exception__username(
    user_storage: UserStorage,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    db_user = await create_user()
    with pytest.raises(EntityAlreadyExistsException):
        await user_storage.create(
            input_dto=CreateUser(
                username=db_user.username,
                email="test@test.com",
            )
        )


async def test__create__entity_already_exists_exception__email(
    user_storage: UserStorage,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    db_user = await create_user()
    with pytest.raises(EntityAlreadyExistsException):
        await user_storage.create(
            input_dto=CreateUser(
                username="test_username",
                email=db_user.email,
            )
        )


async def test__get_by_id(
    user_storage: UserStorage,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    db_user = await create_user()
    user = await user_storage.get_by_id(input_dto=db_user.id)
    assert user == User(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at,
    )


async def test__get_by_id__none(user_storage: UserStorage) -> None:
    assert await user_storage.get_by_id(input_dto=uuid7()) is None


async def test__get_by_id__deleted(
    user_storage: UserStorage,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    db_user = await create_user(deleted_at=now_utc())
    assert await user_storage.get_by_id(input_dto=db_user.id) is None


async def test__get_list(
    user_storage: UserStorage,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    db_users = [await create_user(id=UUID(int=i + 1)) for i in range(3)]
    users = await user_storage.get_list(input_dto=UserListParams(limit=2))
    # Storage fetches one extra row to detect whether another page exists.
    assert [x.id for x in users] == [row.id for row in reversed(db_users)]


async def test__get_list__after(
    user_storage: UserStorage,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    db_users = [await create_user(id=UUID(int=i + 1)) for i in range(3)]
    users = await user_storage.get_list(
        input_dto=UserListParams(limit=1, after=db_users[-1].id)
    )
    assert [x.id for x in users] == [db_users[1].id, db_users[0].id]


async def test__get_list__deleted(
    user_storage: UserStorage,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    await create_user(id=UUID(int=3), deleted_at=now_utc())
    await create_user(id=UUID(int=2))
    users = await user_storage.get_list(input_dto=UserListParams(limit=10))
    assert [x.id for x in users] == [UUID(int=2)]


async def test__get_list__empty_list(user_storage: UserStorage) -> None:
    users = await user_storage.get_list(input_dto=UserListParams(limit=10))
    assert users == []


async def test__exists_by_id(
    user_storage: UserStorage,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    db_user = await create_user()
    assert await user_storage.exists_by_id(input_dto=db_user.id)


async def test__exists_by_id__false(user_storage: UserStorage) -> None:
    assert await user_storage.exists_by_id(input_dto=uuid7()) is False


async def test__exists_by_id__deleted(
    user_storage: UserStorage,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    db_user = await create_user(deleted_at=now_utc())
    assert await user_storage.exists_by_id(input_dto=db_user.id) is False


async def test__update_by_id(
    user_storage: UserStorage,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    db_user = await create_user()
    update_data = UpdateUser(
        id=db_user.id,
        username="test_username",
        email="test@test.com",
    )
    user = await user_storage.update_by_id(input_dto=update_data)
    assert user == User(
        id=db_user.id,
        username=update_data.username,
        email=update_data.email,
        created_at=db_user.created_at,
        updated_at=IsDatetime,
    )


async def test__update_by_id__entity_not_found_exception(
    user_storage: UserStorage,
) -> None:
    with pytest.raises(EntityNotFoundException):
        await user_storage.update_by_id(
            input_dto=UpdateUser(id=uuid7(), username="new_username")
        )


async def test__update_by_id__entity_not_found_exception__deleted(
    user_storage: UserStorage,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    db_user = await create_user(deleted_at=now_utc())
    with pytest.raises(EntityNotFoundException):
        await user_storage.update_by_id(
            input_dto=UpdateUser(id=db_user.id, username="test_username")
        )


async def test__delete_by_id(
    user_storage: UserStorage,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    db_user = await create_user()
    await user_storage.delete_by_id(input_dto=db_user.id)
    assert db_user.deleted_at is not None


async def test__delete_by_id__none(user_storage: UserStorage) -> None:
    assert await user_storage.delete_by_id(input_dto=uuid7()) is None
