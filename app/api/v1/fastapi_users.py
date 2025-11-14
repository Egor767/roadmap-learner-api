from typing import Annotated, TYPE_CHECKING

from fastapi import APIRouter, Depends

from app.core.authentication.fastapi_users import fastapi_users
from app.core.config import settings
from app.core.dependencies import get_users_db
from app.schemas.user_manager import UserRead, UserUpdate

if TYPE_CHECKING:
    from app.models.postgres.user import SQLAlchemyUserDatabase

router = APIRouter(
    prefix=settings.api.v1.users,
    tags=["Users Fastapi"],
)


@router.get(
    "",
    response_model=list[UserRead],
)
async def get_users_list(
    users_db: Annotated[
        "SQLAlchemyUserDatabase",
        Depends(get_users_db),
    ],
) -> list[UserRead]:
    users = await users_db.get_users()
    return [UserRead.model_validate(user) for user in users]


# /me
# /{id}
router.include_router(
    router=fastapi_users.get_users_router(
        UserRead,
        UserUpdate,
    ),
)
