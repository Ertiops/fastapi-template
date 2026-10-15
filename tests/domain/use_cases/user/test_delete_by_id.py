from collections.abc import Awaitable, Callable
from uuid import uuid7

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database.tables import UserTable
from app.application.exceptions import (
    EntityNotFoundException,
)
from app.domain.use_cases.user.delete_by_id import DeleteUserByIdUC
from tests.utils.common import now_utc


async def test__delete_by_id(
    delete_user_by_id_uc: DeleteUserByIdUC,
    create_user: Callable[..., Awaitable[UserTable]],
    session: AsyncSession,
) -> None:
    db_user = await create_user()
    await delete_user_by_id_uc.execute(input_dto=db_user.id)
    await session.refresh(db_user, attribute_names=["deleted_at"])
    assert db_user.deleted_at is not None


async def test__delete_by_id__entity_not_found_exception(
    delete_user_by_id_uc: DeleteUserByIdUC,
) -> None:
    with pytest.raises(EntityNotFoundException):
        await delete_user_by_id_uc.execute(input_dto=uuid7())


async def test__delete_by_id__entity_not_found_exception__deleted(
    delete_user_by_id_uc: DeleteUserByIdUC,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    db_user = await create_user(deleted_at=now_utc())
    with pytest.raises(EntityNotFoundException):
        await delete_user_by_id_uc.execute(input_dto=db_user.id)
