import uuid
from abc import ABC, abstractmethod
from typing import Optional

from app.schemas.user import UserCreateModel, UserBaseModel


class IUserService(ABC):

    @abstractmethod
    async def create_user(self, user_create_model: UserCreateModel) -> UserBaseModel:
        ...

    @abstractmethod
    async def get_user_by_id(self, uid: int) -> UserBaseModel:
        ...

    @abstractmethod
    async def get_user_by_email(self, email: str) -> UserBaseModel:
        ...

    @abstractmethod
    async def auth_user(self, email: str, password: str) -> Optional[UserBaseModel]:
        ...
