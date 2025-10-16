import uuid
from typing import List

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_user_service
from app.core.handlers import router_handler
from app.schemas.user import UserCreate, UserResponse, UserFilters
from app.services.user.service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/create",
             response_model=UserResponse,
             status_code=status.HTTP_201_CREATED)
@router_handler
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    return await user_service.create_user(user_data)


@router.get("/{user_id}",
            response_model=UserResponse,
            status_code=status.HTTP_200_OK)
@router_handler
async def get_user_by_id(
    user_id: uuid.UUID,
    user_service: UserService = Depends(get_user_service)
):
    return await user_service.get_user_by_id(user_id)


@router.get("/search/",
            response_model=List[UserResponse],
            status_code=status.HTTP_200_OK)
@router_handler
async def get_users_by_filters(
    filters: UserFilters = Depends(),
    user_service: UserService = Depends(get_user_service)
):
    return await user_service.get_users_by_filters(filters)

