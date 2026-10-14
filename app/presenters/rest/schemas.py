from collections.abc import Sequence
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, PositiveInt


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class StatusResponseSchema(BaseSchema):
    ok: bool
    status_code: PositiveInt
    message: str


class PaginationSchema(BaseSchema):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    limit: PositiveInt = Field(le=100, default=10)
    after: UUID | None = None


class ItemListSchema[ItemType](BaseSchema):
    items: Sequence[ItemType]
    next_cursor: UUID | None
