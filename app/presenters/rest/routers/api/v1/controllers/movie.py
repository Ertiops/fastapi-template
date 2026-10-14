from http import HTTPStatus
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query, Request

from app.application.exceptions import EmptyPayloadException
from app.domain.entities.movie import (
    CreateMovie,
    MovieListParams,
    UpdateMovie,
)
from app.domain.use_cases.movie.create import CreateMovieUC
from app.domain.use_cases.movie.delete_by_id import DeleteMovieByIdUC
from app.domain.use_cases.movie.get_by_id import GetMovieByIdUC
from app.domain.use_cases.movie.get_list import GetMovieListUC
from app.domain.use_cases.movie.update_by_id import UpdateMovieByIdUC
from app.presenters.rest.routers.api.v1.schemas.movie import (
    CreateMovieSchema,
    MovieListParamsSchema,
    MovieListSchema,
    MovieSchema,
    UpdateMovieSchema,
)
from app.presenters.rest.schemas import reject_duplicate_pagination_params

router = APIRouter(prefix="/movies", tags=["Movies"], route_class=DishkaRoute)


@router.post(
    "/",
    response_model=MovieSchema,
    status_code=HTTPStatus.CREATED,
    name="Create Movie",
)
async def create(
    body: CreateMovieSchema,
    *,
    use_case: FromDishka[CreateMovieUC],
) -> MovieSchema:
    return MovieSchema.model_validate(
        await use_case.execute(input_dto=CreateMovie(**body.model_dump()))
    )


@router.get(
    "/{movie_id:uuid}/",
    response_model=MovieSchema,
    status_code=HTTPStatus.OK,
    name="Get Movie by ID",
)
async def get_by_id(
    movie_id: UUID,
    *,
    use_case: FromDishka[GetMovieByIdUC],
) -> MovieSchema:
    return MovieSchema.model_validate(await use_case.execute(input_dto=movie_id))


@router.get(
    "/",
    response_model=MovieListSchema,
    status_code=HTTPStatus.OK,
    name="Get Movie List",
)
async def get_list(
    request: Request,
    params: MovieListParamsSchema = Query(),
    *,
    use_case: FromDishka[GetMovieListUC],
) -> MovieListSchema:
    reject_duplicate_pagination_params(request)
    return MovieListSchema.model_validate(
        await use_case.execute(input_dto=MovieListParams(**params.model_dump()))
    )


@router.patch(
    "/{movie_id:uuid}/",
    response_model=MovieSchema,
    status_code=HTTPStatus.OK,
    name="Update Movie by ID",
)
async def update_by_id(
    movie_id: UUID,
    body: UpdateMovieSchema,
    *,
    use_case: FromDishka[UpdateMovieByIdUC],
) -> MovieSchema:
    values = body.model_dump(exclude_unset=True)
    if not values:
        raise EmptyPayloadException(message="No values to update")
    return MovieSchema.model_validate(
        await use_case.execute(
            input_dto=UpdateMovie(id=movie_id, **values),
        )
    )


@router.delete(
    "/{movie_id:uuid}/",
    status_code=HTTPStatus.NO_CONTENT,
    name="Delete Movie by ID",
)
async def delete_by_id(
    movie_id: UUID,
    *,
    use_case: FromDishka[DeleteMovieByIdUC],
) -> None:
    await use_case.execute(input_dto=movie_id)
