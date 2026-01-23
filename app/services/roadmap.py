import json
from typing import TYPE_CHECKING

from app.core.handlers import service_handler
from app.core.loggers import roadmap_service_logger as logger
from app.shared.generate_id import generate_base_id
from app.utils.mappers.orm_to_models import roadmap_orm_to_model
from app.utils.mappers.cache_to_model import cache_to_models
from app.utils.cache import key_builder

if TYPE_CHECKING:
    from redis.asyncio import Redis
    from app.core.custom_types import BaseIdType
    from app.services import AccessService
    from app.repositories import RoadmapRepository
    from app.models import User
    from app.schemas.roadmap import (
        RoadmapRead,
        RoadmapCreate,
        RoadmapUpdate,
        RoadmapFilters,
    )


class RoadmapService:
    def __init__(
        self,
        repo: "RoadmapRepository",
        access_service: "AccessService",
        redis: "Redis",
    ):
        self.repo = repo
        self.access = access_service
        self.redis = redis
        self.ttl = 60

    @service_handler
    async def get_all(self) -> list["RoadmapRead"]:
        # get from cache
        cache_key = "roadmaps:all"
        cached = await self.redis.get(cache_key)
        if cached:
            logger.info("Hit cache for key: %r", cache_key)
            return await cache_to_models(cached)

        # get from repository
        db_roadmaps = await self.repo.get_all()
        if not db_roadmaps:
            logger.warning("Roadmaps not found in DB")
            return []

        # validation from orm to model
        validated_roadmaps = [
            await roadmap_orm_to_model(db_roadmap) for db_roadmap in db_roadmaps
        ]

        # set cache
        await self.redis.set(
            cache_key,
            json.dumps([u.model_dump(mode="json") for u in validated_roadmaps]),
            ex=self.ttl,
        )

        return validated_roadmaps

    @service_handler
    async def get_by_filters(
        self,
        current_user: "User",
        filters: "RoadmapFilters",
    ) -> list["RoadmapRead"]:
        filters_dict = filters.model_dump(exclude_none=True, exclude_unset=True)
        # try get from cache only for empty filters (because don't have route /all for get user roadmaps)
        if not filters_dict:
            cache_key = await key_builder(
                func=self.get_by_filters,
                namespace=f"roadmaps:user:{current_user.id}:all",
                args=(),
                kwargs={},
            )
            cached = await self.redis.get(cache_key)
            if cached:
                logger.info("Hit cache for key: %r", cache_key)
                return await cache_to_models(cached)

        # get from repository
        accessed_filters = await self.access.filter_roadmaps_for_user(
            current_user,
            filters_dict,
        )

        db_roadmaps = await self.repo.get_by_filters(accessed_filters)
        if not db_roadmaps:
            logger.warning(
                "Roadmaps with filters(%r) not found",
                filters,
            )
            return []

        # validation from orm to model
        validated_roadmaps = [
            await roadmap_orm_to_model(db_roadmap) for db_roadmap in db_roadmaps
        ]

        # set cache
        if not filters_dict:
            cache_data = json.dumps(
                [u.model_dump(mode="json") for u in validated_roadmaps], default=str
            )
            await self.redis.set(
                cache_key,
                cache_data,
                ex=self.ttl,
            )
            logger.info("Cache SET: %r", cache_key)

        return validated_roadmaps

    @service_handler
    async def get_by_id(
        self,
        current_user: "User",
        roadmap_id: "BaseIdType",
    ) -> "RoadmapRead":
        # try get from cache
        cache_key = await key_builder(
            func=self.get_by_id,
            namespace=f"roadmap:{roadmap_id}:user:{current_user.id}",
            args=(),
            kwargs={},
        )
        cached = await self.redis.get(cache_key)
        if cached:
            logger.info("Hit cache for key: %r", cache_key)
            result_roadmap = await cache_to_models(cached)
            return result_roadmap[0]

        # get from repository
        db_roadmap = await self.repo.get_by_id(roadmap_id)
        if not db_roadmap:
            logger.error("Roadmap(id=%r) not found", roadmap_id)
            raise ValueError("NOT_FOUND")

        # validation from orm to model
        validated_roadmap = await roadmap_orm_to_model(db_roadmap)
        await self.access.ensure_can_view_roadmap(
            current_user, validated_roadmap.model_dump()
        )

        # set in cache
        await self.redis.set(
            cache_key,
            json.dumps([validated_roadmap.model_dump(mode="json")]),
            ex=self.ttl,
        )

        return validated_roadmap

    @service_handler
    async def create(
        self,
        current_user: "User",
        roadmap_create_data: "RoadmapCreate",
    ) -> "RoadmapRead":
        # create in repo
        roadmap_dict = roadmap_create_data.model_dump()
        roadmap_dict["user_id"] = current_user.id
        roadmap_dict["id"] = await generate_base_id()

        created_roadmap = await self.repo.create(roadmap_dict)
        if not created_roadmap:
            logger.error(
                "Roadmap with params(%r) for User(id=%r) not created",
                roadmap_create_data,
                current_user.id,
            )
            raise ValueError("OPERATION_FAILED")

        validated_created_roadmap = await roadmap_orm_to_model(created_roadmap)

        # clear cache for list of user roadmaps
        user_filter_keys = await self.redis.keys(f"roadmaps:user:{current_user.id}:*")
        if user_filter_keys:
            await self.redis.delete(*user_filter_keys)

        return validated_created_roadmap

    @service_handler
    async def delete(
        self,
        current_user: "User",
        roadmap_id: "BaseIdType",
    ) -> None:
        await self.get_by_id(current_user, roadmap_id)

        success = await self.repo.delete(roadmap_id)
        if success:
            logger.info("Roadmap(id=%r) was deleted successfully", roadmap_id)
        else:
            logger.error("Failed to delete Roadmap(id=%r)", roadmap_id)
            raise ValueError("OPERATION_FAILED")

        # clear cache for list of user roadmaps
        user_filter_keys = await self.redis.keys(f"roadmaps:user:{current_user.id}:*")
        if user_filter_keys:
            await self.redis.delete(*user_filter_keys)

        # clear cache for user specific roadmap
        detail_keys = await self.redis.keys(
            f"roadmap:{roadmap_id}:user:{current_user.id}:*"
        )
        if detail_keys:
            await self.redis.delete(*detail_keys)

    @service_handler
    async def update(
        self,
        current_user: "User",
        roadmap_id: "BaseIdType",
        roadmap_update_data: "RoadmapUpdate",
    ) -> "RoadmapRead":
        await self.get_by_id(current_user, roadmap_id)

        roadmap_dict = roadmap_update_data.model_dump(exclude_unset=True)

        updated_roadmap = await self.repo.update(roadmap_id, roadmap_dict)
        if not updated_roadmap:
            logger.error("Failed to update Roadmap(id=%r)", roadmap_id)
            raise ValueError("OPERATION_FAILED")

        validated_updated_roadmap = await roadmap_orm_to_model(updated_roadmap)

        # clear cache for list of user roadmaps
        user_filter_keys = await self.redis.keys(f"roadmaps:user:{current_user.id}:*")
        if user_filter_keys:
            await self.redis.delete(*user_filter_keys)

        # clear cache for user specific roadmap
        detail_keys = await self.redis.keys(
            f"roadmap:{roadmap_id}:user:{current_user.id}:*"
        )
        if detail_keys:
            await self.redis.delete(*detail_keys)

        return validated_updated_roadmap
