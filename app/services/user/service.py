import uuid
from typing import Optional

from app.core.logging import user_logger as logger
from app.core.security import get_password_hash, verify_password
from app.repositories.user.interface import IUserRepository
from app.schemas.user import UserCreateModel, UserBaseModel
from app.services.user.interface import IUserService


class UserService(IUserService):
    def __init__(self, repo: IUserRepository):
        self.repo = repo

    async def create_user(self, user_create_model: UserCreateModel) -> UserBaseModel:
        try:
            existing_user = await self.repo.get_user_by_email(user_create_model.email)
            if existing_user:
                logger.warning(f"Attempt to create user with existing email: {user_create_model.email}")
                raise ValueError("User with this email already exists")

            hashed_password = get_password_hash(user_create_model.password)
            user_data = user_create_model.model_dump()
            user_data["hashed_password"] = hashed_password
            del user_data["password"]

            logger.info(f"Creating new user: {user_create_model.email}")
            created_user = await self.repo.create_user(UserInDB(**user_data))

            logger.info(f"User created successfully: {created_user.id}")
            return UserBaseModel.model_validate(created_user)

        except Exception as e:
            logger.error(f"Error creating user {user_create_model.email}: {str(e)}")
            raise

    async def get_user_by_id(self, uid: uuid.UUID) -> UserBaseModel:

        try:
            user = await self.repo.get_user_by_id(uid)
            if not user:
                logger.warning(f"User not found with id: {uid}")
                raise ValueError("User not found")

            logger.debug(f"Retrieved user by id: {uid}")
            return UserBaseModel.model_validate(user)

        except Exception as e:
            logger.error(f"Error retrieving user {uid}: {str(e)}")
            raise

    async def get_user_by_email(self, email: str) -> Optional[UserBaseModel]:
        try:
            user = await self.repo.get_user_by_email(email)
            if user:
                return UserBaseModel.model_validate(user)
            return None
        except Exception as e:
            logger.error(f"Error retrieving user by email {email}: {str(e)}")
            raise

    async def auth_user(self, email: str, password: str) -> Optional[UserBaseModel]:
        try:
            user = await self.repo.get_user_by_email(email)
            if not user:
                return None

            if not verify_password(password, user.hashed_password):
                logger.warning(f"Failed authentication attempt for user: {email}")
                return None

            logger.info(f"User authenticated successfully: {email}")
            return UserBaseModel.model_validate(user)

        except Exception as e:
            logger.error(f"Error during authentication for {email}: {str(e)}")
            raise

