import json
from typing import TYPE_CHECKING

from app.core.handlers import service_handler
from app.core.loggers import block_service_logger as logger
from app.shared.access import (
    user_can_read_entity,
    get_accessed_filters,
)
from app.shared.generate_id import generate_base_id
from app.utils.cache import key_builder
from app.utils.mappers.cache_to_model import block_cache_to_models
from app.utils.mappers.orm_to_models import block_orm_to_model

if TYPE_CHECKING:
    from redis.asyncio import Redis
    from app.core.custom_types import BaseIdType
    from app.repositories.block import BlockRepository
    from app.models import User
    from app.schemas.block import (
        BlockCreate,
        BlockRead,
        BlockUpdate,
        BlockFilters,
    )


class BlockService:
    def __init__(
        self,
        repo: "BlockRepository",
        redis: "Redis",
    ):
        self.repo = repo
        self.redis = redis
        self.ttl = 60

    @service_handler
    async def get_all(self) -> list["BlockRead"]:
        cache_key = "blocks:all"
        cached = await self.redis.get(cache_key)
        if cached:
            logger.info("Hit cache for key: %r", cache_key)
            return await block_cache_to_models(cached)

        db_blocks = await self.repo.get_all()
        if not db_blocks:
            logger.warning("Blocks not found in DB")
            return []

        validated_blocks = [
            await block_orm_to_model(db_block) for db_block in db_blocks
        ]

        await self.redis.set(
            cache_key,
            json.dumps([u.model_dump(mode="json") for u in validated_blocks]),
            ex=self.ttl,
        )

        return validated_blocks

    @service_handler
    async def get_by_filters(
        self,
        current_user: "User",
        filters: "BlockFilters",
    ) -> list["BlockRead"]:
        filters_dict = filters.model_dump(
            exclude_none=True,
            exclude_unset=True,
        )

        if not filters_dict:
            cache_key = await key_builder(
                func=self.get_by_filters,
                namespace=f"blocks:user:{current_user.id}:all",
                args=(),
                kwargs={},
            )
            cached = await self.redis.get(cache_key)
            if cached:
                logger.info("Hit cache for key: %r", cache_key)
                return await block_cache_to_models(cached)

        accessed_filters = await get_accessed_filters(
            current_user,
            filters_dict,
        )

        db_blocks = await self.repo.get_by_filters(accessed_filters)
        if not db_blocks:
            logger.warning("Blocks with filters(%r) not found", filters)
            return []

        validated_blocks = [
            await block_orm_to_model(db_block) for db_block in db_blocks
        ]

        if not filters_dict:
            cache_data = json.dumps(
                [u.model_dump(mode="json") for u in validated_blocks], default=str
            )
            await self.redis.set(
                cache_key,
                cache_data,
                ex=self.ttl,
            )
            logger.info("Cache SET: %r", cache_key)

        return validated_blocks

    @service_handler
    async def get_by_id(
        self,
        current_user: "User",
        block_id: "BaseIdType",
    ) -> "BlockRead":
        cache_key = await key_builder(
            func=self.get_by_id,
            namespace=f"block:{block_id}:user:{current_user.id}",
            args=(),
            kwargs={},
        )
        cached = await self.redis.get(cache_key)
        if cached:
            logger.info("Hit cache for key: %r", cache_key)
            result_roadmap = await block_cache_to_models(cached)
            return result_roadmap[0]

        db_block = await self.repo.get_by_id(block_id)
        if not db_block:
            logger.warning("Block(%r) not found", block_id)
            raise ValueError("NOT_FOUND")

        validated_block = await block_orm_to_model(db_block)
        await user_can_read_entity(
            current_user,
            validated_block.model_dump(),
        )

        await self.redis.set(
            cache_key,
            json.dumps([validated_block.model_dump(mode="json")]),
            ex=self.ttl,
        )

        return validated_block

    @service_handler
    async def create(
        self,
        current_user: "User",
        block_create_data: "BlockCreate",
    ) -> "BlockRead":
        block_dict = block_create_data.model_dump()
        block_dict["id"] = await generate_base_id()
        block_dict["user_id"] = current_user.id

        created_block = await self.repo.create(block_dict)
        if not created_block:
            logger.error(
                "Block with params(%r) for User(id=%r) not created",
                block_create_data,
                current_user.id,
            )
            raise ValueError("OPERATION_FAILED")

        validated_created_block = await block_orm_to_model(created_block)

        user_filter_keys = await self.redis.keys(f"roadmaps:user:{current_user.id}:*")
        all_key = await self.redis.keys(f"blocks:all")
        summary_keys = user_filter_keys + all_key
        if summary_keys:
            await self.redis.delete(*summary_keys)

        return validated_created_block

    @service_handler
    async def delete(
        self,
        current_user: "User",
        block_id: "BaseIdType",
    ) -> None:
        await self.get_by_id(current_user, block_id)

        success = await self.repo.delete(block_id)
        if success:
            logger.info("Block deleted successfully: %r", block_id)
        else:
            logger.error("Deletion for Block(%r) FAILED", block_id)
            raise ValueError("OPERATION_FAILED")

        user_filter_keys = await self.redis.keys(f"blocks:user:{current_user.id}:*")
        detail_keys = await self.redis.keys(
            f"block:{block_id}:user:{current_user.id}:*"
        )
        all_key = await self.redis.keys("blocks:all")
        summary_keys = user_filter_keys + all_key + detail_keys
        if summary_keys:
            await self.redis.delete(*summary_keys)

    @service_handler
    async def update(
        self,
        current_user: "User",
        block_id: "BaseIdType",
        block_update_data: "BlockUpdate",
    ) -> "BlockRead":
        await self.get_by_id(current_user, block_id)

        block_dict = block_update_data.model_dump(exclude_unset=True)

        updated_block = await self.repo.update(block_id, block_dict)
        if not updated_block:
            logger.error("Failed to update Block(id=%r)", block_id)
            raise ValueError("OPERATION_FAILED")

        validated_updated_user = await block_orm_to_model(updated_block)

        user_filter_keys = await self.redis.keys(f"blocks:user:{current_user.id}:*")
        detail_keys = await self.redis.keys(
            f"block:{block_id}:user:{current_user.id}:*"
        )
        all_key = await self.redis.keys("blocks:all")
        summary_keys = user_filter_keys + all_key + detail_keys
        if summary_keys:
            await self.redis.delete(*summary_keys)

        return validated_updated_user
