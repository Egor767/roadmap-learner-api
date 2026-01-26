import json
from typing import TYPE_CHECKING

from app.core.handlers import service_handler
from app.core.loggers import card_service_logger as logger
from app.shared.access import get_accessed_filters, user_can_read_entity
from app.shared.generate_id import generate_base_id
from app.utils.cache import key_builder
from app.utils.mappers.cache_to_model import card_cache_to_models
from app.utils.mappers.orm_to_models import card_orm_to_model

if TYPE_CHECKING:
    from redis.asyncio import Redis
    from app.core.custom_types import BaseIdType
    from app.repositories import CardRepository
    from app.models import User
    from app.schemas.card import (
        CardRead,
        CardCreate,
        CardUpdate,
        CardFilters,
    )


class CardService:
    def __init__(
        self,
        repo: "CardRepository",
        redis: "Redis",
    ):
        self.repo = repo
        self.redis = redis
        self.ttl = 60

    @service_handler
    async def get_all(self) -> list["CardRead"]:
        cache_key = "cards:all"
        cached = await self.redis.get(cache_key)
        if cached:
            logger.info("Hit cache for key: %r", cache_key)
            return await card_cache_to_models(cached)

        db_cards = await self.repo.get_all()
        if not db_cards:
            logger.warning("Cards not found in DB")
            return []

        validated_cards = [await card_orm_to_model(db_card) for db_card in db_cards]

        await self.redis.set(
            cache_key,
            json.dumps([u.model_dump(mode="json") for u in validated_cards]),
            ex=self.ttl,
        )

        return validated_cards

    @service_handler
    async def get_by_filters(
        self,
        current_user: "User",
        filters: "CardFilters",
    ) -> list["CardRead"]:
        filters_dict = filters.model_dump(
            exclude_none=True,
            exclude_unset=True,
        )

        if not filters_dict:
            cache_key = await key_builder(
                func=self.get_by_filters,
                namespace=f"cards:user:{current_user.id}:all",
                args=(),
                kwargs={},
            )
            cached = await self.redis.get(cache_key)
            if cached:
                logger.info("Hit cache for key: %r", cache_key)
                return await card_cache_to_models(cached)

        accessed_filters = await get_accessed_filters(
            current_user,
            filters_dict,
        )

        db_cards = await self.repo.get_by_filters(accessed_filters)
        if not db_cards:
            logger.warning("Cards with filters(%r) not found", filters)
            return []

        validated_cards = [await card_orm_to_model(db_card) for db_card in db_cards]

        if not filters_dict:
            cache_data = json.dumps(
                [u.model_dump(mode="json") for u in validated_cards],
                default=str,
            )
            await self.redis.set(
                cache_key,
                cache_data,
                ex=self.ttl,
            )
            logger.info("Cache SET: %r", cache_key)

        return validated_cards

    @service_handler
    async def get_by_id(
        self,
        current_user: "User",
        card_id: "BaseIdType",
    ) -> "CardRead":
        cache_key = await key_builder(
            func=self.get_by_id,
            namespace=f"card:{card_id}:user:{current_user.id}",
            args=(),
            kwargs={},
        )
        cached = await self.redis.get(cache_key)
        if cached:
            logger.info("Hit cache for key: %r", cache_key)
            result_roadmap = await card_cache_to_models(cached)
            return result_roadmap[0]

        db_card = await self.repo.get_by_id(card_id)
        if not db_card:
            logger.error(f"Card(%r) not found or access denied", card_id)
            raise ValueError("NOT_FOUND")

        validated_card = await card_orm_to_model(db_card)
        await user_can_read_entity(
            current_user,
            validated_card.model_dump(),
        )

        await self.redis.set(
            cache_key,
            json.dumps([validated_card.model_dump(mode="json")]),
            ex=self.ttl,
        )

        return validated_card

    @service_handler
    async def create(
        self,
        current_user: "User",
        card_create_data: "CardCreate",
    ) -> "CardRead":
        card_dict = card_create_data.model_dump()
        card_dict["id"] = await generate_base_id()
        card_dict["user_id"] = current_user.id

        created_card = await self.repo.create(card_dict)
        if not created_card:
            logger.error(
                "Card with params(%r) for User(id=%r) not created",
                card_create_data,
                current_user.id,
            )
            raise ValueError("OPERATION_FAILED")

        validated_created_card = await card_orm_to_model(created_card)

        user_filter_keys = await self.redis.keys(f"cards:user:{current_user.id}:*")
        all_key = await self.redis.keys(f"cards:all")
        summary_keys = user_filter_keys + all_key
        if summary_keys:
            await self.redis.delete(*summary_keys)

        return validated_created_card

    @service_handler
    async def delete(
        self,
        current_user: "User",
        card_id: "BaseIdType",
    ) -> None:
        await self.get_by_id(current_user, card_id)

        success = await self.repo.delete(card_id)
        if success:
            logger.info("Card deleted successfully: %r", card_id)
        else:
            logger.error("Deletion for Card(%r) FAILED", card_id)
            raise ValueError("OPERATION_FAILED")

        user_filter_keys = await self.redis.keys(f"cards:user:{current_user.id}:*")
        detail_keys = await self.redis.keys(f"card:{card_id}:user:{current_user.id}:*")
        all_key = await self.redis.keys("cards:all")
        summary_keys = user_filter_keys + all_key + detail_keys
        if summary_keys:
            await self.redis.delete(*summary_keys)

    @service_handler
    async def update(
        self,
        current_user: "User",
        card_id: "BaseIdType",
        card_update_data: "CardUpdate",
    ) -> "CardRead":
        await self.get_by_id(current_user, card_id)

        card_dict = card_update_data.model_dump(exclude_unset=True)

        updated_card = await self.repo.update(card_id, card_dict)
        if not updated_card:
            logger.warning("Failed to update Block(id=%r)", card_id)
            raise ValueError("OPERATION_FAILED")

        validated_updated_card = await card_orm_to_model(updated_card)

        user_filter_keys = await self.redis.keys(f"cards:user:{current_user.id}:*")
        detail_keys = await self.redis.keys(f"card:{card_id}:user:{current_user.id}:*")
        all_key = await self.redis.keys("cards:all")
        summary_keys = user_filter_keys + all_key + detail_keys
        if summary_keys:
            await self.redis.delete(*summary_keys)

        return validated_updated_card
