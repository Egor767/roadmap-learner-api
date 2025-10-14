import uuid
from typing import Optional

from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.postgre.user import User
from app.repositories.user.interface import IUserRepository
from app.schemas.user import UserInDB


class UserRepository(IUserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, user: UserInDB) -> UserInDB:
        try:
            user_data = user.model_dump()

            stmt = insert(User).values(**user_data).returning(User)
            result = await self.session.execute(stmt)
            db_user = result.scalar_one()

            await self.session.commit()

            return UserInDB(
                id=db_user.id,
                email=db_user.email,
                first_name=db_user.first_name,
                last_name=db_user.last_name,
                hashed_password=db_user.hashed_password,
                is_active=db_user.is_active,
                created_at=db_user.created_at,
                updated_at=db_user.updated_at
            )

        except Exception as e:
            await self.session.rollback()
            raise e

    async def get_user_by_id(self, uid: uuid.UUID) -> Optional[UserInDB]:
        try:
            stmt = select(User).where(User.id == uid, User.is_active == True)
            result = await self.session.execute(stmt)
            db_user = result.scalar_one_or_none()

            if not db_user:
                return None

            return UserInDB(
                id=db_user.id,
                email=db_user.email,
                first_name=db_user.first_name,
                last_name=db_user.last_name,
                hashed_password=db_user.hashed_password,
                is_active=db_user.is_active,
                created_at=db_user.created_at,
                updated_at=db_user.updated_at
            )

        except Exception as e:
            raise e

    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        try:
            stmt = select(User).where(User.email == email, User.is_active == True)
            result = await self.session.execute(stmt)
            db_user = result.scalar_one_or_none()

            if not db_user:
                return None

            return UserInDB(
                id=db_user.id,
                email=db_user.email,
                first_name=db_user.first_name,
                last_name=db_user.last_name,
                hashed_password=db_user.hashed_password,
                is_active=db_user.is_active,
                created_at=db_user.created_at,
                updated_at=db_user.updated_at
            )

        except Exception as e:
            raise e

    async def update_user(self, uid: uuid.UUID, user_update: dict) -> Optional[UserInDB]:
        try:
            stmt = select(User).where(User.id == uid)
            result = await self.session.execute(stmt)
            db_user = result.scalar_one_or_none()

            if not db_user:
                return None

            for field, value in user_update.items():
                setattr(db_user, field, value)

            await self.session.commit()

            return UserInDB(
                id=db_user.id,
                email=db_user.email,
                first_name=db_user.first_name,
                last_name=db_user.last_name,
                hashed_password=db_user.hashed_password,
                is_active=db_user.is_active,
                created_at=db_user.created_at,
                updated_at=db_user.updated_at
            )

        except Exception as e:
            await self.session.rollback()
            raise e

    async def delete_user(self, uid: uuid.UUID) -> bool:
        try:
            stmt = select(User).where(User.id == uid)
            result = await self.session.execute(stmt)
            db_user = result.scalar_one_or_none()

            if not db_user:
                return False

            db_user.is_active = False
            await self.session.commit()
            return True

        except Exception as e:
            await self.session.rollback()
            raise e

