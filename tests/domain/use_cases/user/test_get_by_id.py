from collections.abc import Awaitable, Callable
from uuid import uuid7

import pytest

from app.adapters.database.tables import UserTable
from app.application.exceptions import (
    EntityNotFoundException,
)
from app.domain.entities.user import (
    User,
)
from app.domain.use_cases.user.get_by_id import GetUserByIdUC
from tests.utils.common import now_utc


async def test__get_by_id(
    get_user_by_id_uc: GetUserByIdUC,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    db_user = await create_user()
    user = await get_user_by_id_uc.execute(input_dto=db_user.id)
    assert user == User(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at,
    )


async def test__get_by_id__entity_not_found_exception(
    get_user_by_id_uc: GetUserByIdUC,
) -> None:
    with pytest.raises(EntityNotFoundException):
        await get_user_by_id_uc.execute(input_dto=uuid7())


async def test__get_by_id__entity_not_found_exception__deleted(
    get_user_by_id_uc: GetUserByIdUC,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    db_user = await create_user(deleted_at=now_utc())
    with pytest.raises(EntityNotFoundException):
        await get_user_by_id_uc.execute(input_dto=db_user.id)
