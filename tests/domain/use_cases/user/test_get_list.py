from collections.abc import Awaitable, Callable
from uuid import UUID

import pytest

from app.adapters.database.tables import UserTable
from app.domain.entities.common import ItemList
from app.domain.entities.user import User, UserListParams
from app.domain.use_cases.user.get_list import GetUserListUC


async def test__get_list(
    get_user_list_uc: GetUserListUC,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    db_users = [await create_user(id=UUID(int=i + 1)) for i in range(3)]
    result = await get_user_list_uc.execute(input_dto=UserListParams(limit=10))
    assert result == ItemList(
        items=[
            User(
                id=db_user.id,
                username=db_user.username,
                email=db_user.email,
                created_at=db_user.created_at,
                updated_at=db_user.updated_at,
            )
            for db_user in reversed(db_users)
        ],
        next_cursor=None,
    )


@pytest.mark.parametrize(
    ("after", "expected_id", "expected_cursor"),
    [
        (None, UUID(int=3), UUID(int=3)),
        (UUID(int=3), UUID(int=2), UUID(int=2)),
        (UUID(int=2), UUID(int=1), None),
    ],
)
async def test__get_list__limit_and_cursor(
    get_user_list_uc: GetUserListUC,
    create_user: Callable[..., Awaitable[UserTable]],
    after: UUID | None,
    expected_id: UUID,
    expected_cursor: UUID | None,
) -> None:
    for value in (1, 2, 3):
        await create_user(id=UUID(int=value))
    result = await get_user_list_uc.execute(
        input_dto=UserListParams(limit=1, after=after)
    )
    assert ([user.id for user in result.items], result.next_cursor) == (
        [expected_id],
        expected_cursor,
    )


async def test__get_list__exactly_full_last_page(
    get_user_list_uc: GetUserListUC,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    db_users = [await create_user(id=UUID(int=i + 1)) for i in range(2)]
    result = await get_user_list_uc.execute(input_dto=UserListParams(limit=2))
    assert ([user.id for user in result.items], result.next_cursor) == (
        [user.id for user in reversed(db_users)],
        None,
    )


async def test__get_list__empty_list(get_user_list_uc: GetUserListUC) -> None:
    result = await get_user_list_uc.execute(input_dto=UserListParams(limit=10))
    assert result == ItemList(items=[], next_cursor=None)


async def test__get_list__absent_anchor(
    get_user_list_uc: GetUserListUC,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    await create_user(id=UUID(int=5))
    result = await get_user_list_uc.execute(
        input_dto=UserListParams(limit=10, after=UUID(int=8))
    )
    assert ([user.id for user in result.items], result.next_cursor) == (
        [UUID(int=5)],
        None,
    )
