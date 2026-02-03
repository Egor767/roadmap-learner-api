import json
import logging
from typing import TYPE_CHECKING

from redis.asyncio import Redis

from app.core.handlers import service_handler
from app.core.loggers import user_service_logger as logger
from app.shared.access import get_accessed_filters
from app.utils.mappers.cache_to_model import users_cache_to_model
from app.utils.mappers.orm_to_models import user_orm_to_model

if TYPE_CHECKING:
    from app.repositories import UserRepository
    from app.schemas.user import UserRead, UserFilters
    from app.models import User


class UserService:
    def __init__(
        self,
        repo: "UserRepository",
        redis: "Redis",
    ):
        self.repo = repo
        self.redis = redis
        self.ttl = 60

    @service_handler
    async def get_all(self) -> list["UserRead"]:
        cache_key = "users:all"
        cached = await self.redis.get(cache_key)
        if cached:
            logging.info("Hit cache for key: %r", cache_key)
            return await users_cache_to_model(cached)

        db_users = await self.repo.get_all()
        if len(db_users) == 0:
            logger.warning("Users not found in DB")
            return []

        validated_users = [await user_orm_to_model(user) for user in db_users]
        await self.redis.set(
            cache_key,
            json.dumps([u.model_dump_json() for u in validated_users]),
            ex=self.ttl,
        )
        return validated_users

    @service_handler
    async def get_by_filters(
        self,
        current_user: "User",
        filters: "UserFilters",
    ) -> list["UserRead"]:
        filters_dict = filters.model_dump()
        accessed_filters = await get_accessed_filters(
            current_user,
            filters_dict,
        )

        db_users = await self.repo.get_by_filters(accessed_filters)
        if len(db_users) == 0:
            logger.warning("Users with filters(%r) not found", filters)
            return []

        validated_users = [await user_orm_to_model(user) for user in db_users]

        return validated_users
