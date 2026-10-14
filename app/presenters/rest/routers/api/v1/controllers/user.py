from http import HTTPStatus
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query

from app.application.exceptions import EmptyPayloadException
from app.domain.entities.user import (
    CreateUser,
    UpdateUser,
    UserListParams,
)
from app.domain.use_cases.user.create import CreateUserUC
from app.domain.use_cases.user.delete_by_id import DeleteUserByIdUC
from app.domain.use_cases.user.get_by_id import GetUserByIdUC
from app.domain.use_cases.user.get_list import GetUserListUC
from app.domain.use_cases.user.update_by_id import UpdateUserByIdUC
from app.presenters.rest.routers.api.v1.schemas.user import (
    CreateUserSchema,
    UpdateUserSchema,
    UserListParamsSchema,
    UserListSchema,
    UserSchema,
)

router = APIRouter(prefix="/users", tags=["Users"], route_class=DishkaRoute)


@router.post(
    "/",
    response_model=UserSchema,
    status_code=HTTPStatus.CREATED,
    name="Create User",
)
async def create(
    body: CreateUserSchema,
    *,
    use_case: FromDishka[CreateUserUC],
) -> UserSchema:
    return UserSchema.model_validate(
        await use_case.execute(
            input_dto=CreateUser(**body.model_dump()),
        )
    )


@router.get(
    "/{user_id:uuid}/",
    response_model=UserSchema,
    status_code=HTTPStatus.OK,
    name="Get User by ID",
)
async def get_by_id(
    user_id: UUID,
    *,
    use_case: FromDishka[GetUserByIdUC],
) -> UserSchema:
    return UserSchema.model_validate(await use_case.execute(input_dto=user_id))


@router.get(
    "/",
    response_model=UserListSchema,
    status_code=HTTPStatus.OK,
    name="Get User List",
)
async def get_list(
    params: UserListParamsSchema = Query(),
    *,
    use_case: FromDishka[GetUserListUC],
) -> UserListSchema:
    return UserListSchema.model_validate(
        await use_case.execute(
            input_dto=UserListParams(**params.model_dump()),
        )
    )


@router.patch(
    "/{user_id:uuid}/",
    response_model=UserSchema,
    status_code=HTTPStatus.OK,
    name="Update User by ID",
)
async def update_by_id(
    user_id: UUID,
    body: UpdateUserSchema,
    *,
    use_case: FromDishka[UpdateUserByIdUC],
) -> UserSchema:
    values = body.model_dump(exclude_unset=True)
    if not values:
        raise EmptyPayloadException(message="No values to update")
    return UserSchema.model_validate(
        await use_case.execute(
            input_dto=UpdateUser(id=user_id, **values),
        )
    )


@router.delete(
    "/{user_id:uuid}/",
    status_code=HTTPStatus.NO_CONTENT,
    name="Delete User by ID",
)
async def delete_by_id(
    user_id: UUID,
    *,
    use_case: FromDishka[DeleteUserByIdUC],
) -> None:
    await use_case.execute(input_dto=user_id)
