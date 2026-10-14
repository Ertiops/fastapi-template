from collections.abc import Awaitable, Callable
from uuid import uuid7

import pytest
from dirty_equals import IsDatetime

from app.adapters.database.tables import UserTable
from app.application.exceptions import (
    EntityNotFoundException,
)
from app.domain.entities.user import (
    UpdateUser,
    User,
)
from app.domain.use_cases.user.update_by_id import UpdateUserByIdUC
from tests.utils.common import now_utc


async def test__update_by_id(
    update_user_by_id_uc: UpdateUserByIdUC,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    db_user = await create_user()
    update_data = UpdateUser(
        id=db_user.id,
        username="test_username",
        email="test@test.com",
    )
    user = await update_user_by_id_uc.execute(input_dto=update_data)
    assert user == User(
        id=db_user.id,
        username=update_data.username,
        email=update_data.email,
        created_at=db_user.created_at,
        updated_at=IsDatetime,
    )


async def test__update_by_id__entity_not_found_exception(
    update_user_by_id_uc: UpdateUserByIdUC,
) -> None:
    with pytest.raises(EntityNotFoundException):
        await update_user_by_id_uc.execute(
            input_dto=UpdateUser(id=uuid7(), username="test_username")
        )


async def test__update_by_id__entity_not_found_exception__deleted(
    update_user_by_id_uc: UpdateUserByIdUC,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    db_user = await create_user(deleted_at=now_utc())
    with pytest.raises(EntityNotFoundException):
        await update_user_by_id_uc.execute(
            input_dto=UpdateUser(id=db_user.id, username="test_username")
        )
