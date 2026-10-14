from collections.abc import Sequence
from uuid import UUID

from fastapi import Request
from fastapi.exceptions import RequestValidationError
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


def reject_duplicate_pagination_params(request: Request) -> None:
    """Do not silently choose one of several values for a cursor or page size."""
    for name in ("limit", "after"):
        values = request.query_params.getlist(name)
        if len(values) > 1:
            raise RequestValidationError(
                [
                    {
                        "type": "duplicate_parameter",
                        "loc": ("query", name),
                        "msg": f"Query parameter '{name}' may appear only once",
                        "input": values,
                    }
                ]
            )
