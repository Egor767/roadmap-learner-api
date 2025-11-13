from fastapi import APIRouter

from app.core.authentication.fastapi_users import fastapi_users
from app.core.config import settings
from app.schemas.user_manager import UserRead, UserUpdate

router = APIRouter(
    prefix=settings.api.v1.users,
    tags=["Users"],
)


# /me
# /{id}
router.include_router(
    router=fastapi_users.get_users_router(
        UserRead,
        UserUpdate,
    ),
)
