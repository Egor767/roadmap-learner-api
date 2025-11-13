from typing import Optional

from fastapi_users import schemas

from app.core.types import BaseIdType


class UserRead(schemas.BaseUser[BaseIdType]):
    username: str


class UserCreate(schemas.BaseUserCreate):
    username: Optional[str] = None


class UserUpdate(schemas.BaseUserUpdate):
    username: str
