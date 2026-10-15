from typing import Protocol
from uuid import UUID

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute


class HasUUID(Protocol):
    @property
    def id(self) -> UUID: ...


async def fetch_uuid_page[T: HasUUID](
    *,
    session: AsyncSession,
    statement: Select[tuple[T]],
    id_column: InstrumentedAttribute[UUID],
    limit: int,
    after: UUID | None,
) -> tuple[list[T], UUID | None]:
    if limit < 1:
        raise ValueError("limit must be positive")

    if after is not None:
        statement = statement.where(id_column < after)

    statement = statement.order_by(None).order_by(id_column.desc()).limit(limit + 1)
    rows = list(await session.scalars(statement))

    has_next = len(rows) > limit
    if has_next:
        rows.pop()

    return rows, rows[-1].id if has_next else None
