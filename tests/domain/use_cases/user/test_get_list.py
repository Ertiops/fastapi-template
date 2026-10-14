from collections.abc import Awaitable, Callable
from uuid import UUID

from app.adapters.database.tables import UserTable
from app.domain.entities.common import ItemList
from app.domain.entities.user import UserListParams
from app.domain.use_cases.user.get_list import GetUserListUC


async def test__get_list(
    get_user_list_uc: GetUserListUC,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    db_users = [await create_user(id=UUID(int=i + 1)) for i in range(3)]
    result = await get_user_list_uc.execute(input_dto=UserListParams(limit=10))
    assert isinstance(result, ItemList)
    assert [user.id for user in result.items] == [row.id for row in reversed(db_users)]
    assert result.next_cursor is None


async def test__get_list__limit_and_cursor(
    get_user_list_uc: GetUserListUC,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    db_users = [await create_user(id=UUID(int=i + 1)) for i in range(3)]
    first = await get_user_list_uc.execute(input_dto=UserListParams(limit=1))
    assert [user.id for user in first.items] == [db_users[-1].id]
    assert first.next_cursor == db_users[-1].id
    second = await get_user_list_uc.execute(
        input_dto=UserListParams(limit=1, after=first.next_cursor)
    )
    assert [user.id for user in second.items] == [db_users[-2].id]
    assert second.next_cursor == db_users[-2].id
    last = await get_user_list_uc.execute(
        input_dto=UserListParams(limit=1, after=second.next_cursor)
    )
    assert [user.id for user in last.items] == [db_users[0].id]
    assert last.next_cursor is None


async def test__get_list__exactly_full_last_page(
    get_user_list_uc: GetUserListUC,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    await create_user()
    await create_user()
    result = await get_user_list_uc.execute(input_dto=UserListParams(limit=2))
    assert len(result.items) == 2
    assert result.next_cursor is None


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
    assert [user.id for user in result.items] == [UUID(int=5)]
    assert result.next_cursor is None
