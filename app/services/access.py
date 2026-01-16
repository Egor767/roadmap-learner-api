import logging
from typing import TYPE_CHECKING

from app.utils.mappers.orm_to_models import block_orm_to_model

if TYPE_CHECKING:
    from app.core.custom_types import BaseIdType
    from app.repositories import (
        RoadmapRepository,
        BlockRepository,
        CardRepository,
    )
    from app.models import User


logger = logging.getLogger("AccessService-Logger")


class AccessService:
    def __init__(
        self,
        roadmap_repo: "RoadmapRepository",
        block_repo: "BlockRepository",
        card_repo: "CardRepository",
    ):
        self.roadmap_repo = roadmap_repo
        self.block_repo = block_repo
        self.card_repo = card_repo

    @staticmethod
    async def filter_users_for_user(
        user: "User",
        filters: dict,
    ) -> dict:

        if user.is_superuser:
            return filters

        if not filters.get("id"):
            filters["id"] = user.id
            return filters

        if filters.get("id") == user.id:
            return filters

        logger.error(
            "Access denied to User with filters(%r) for User(id=%r)",
            filters,
            user.id,
        )
        raise PermissionError("Forbidden")

    @staticmethod
    async def filter_roadmaps_for_user(
        user: "User",
        filters: dict,
    ) -> dict:
        logger.info("filters = %r", filters)
        if user.is_superuser:
            return filters

        if not filters.get("user_id"):
            filters["user_id"] = user.id
            return filters

        if filters.get("user_id") == user.id:
            return filters

        logger.error(
            "Access denied to Roadmaps with filters(%r) for User(id=%r)",
            filters,
            user.id,
        )
        raise PermissionError("Forbidden")

    @staticmethod
    async def ensure_can_view_roadmap(
        user: "User",
        roadmap: dict,
    ) -> None:

        if user.is_superuser or user.id == roadmap.get("user_id"):
            return

        logger.error(
            "Access denied to Roadmap(id=%r) for User(id=%r)",
            roadmap.get("user_id"),
            user.id,
        )
        raise PermissionError("Forbidden")

    async def ensure_can_view_roadmap_by_id(
        self,
        user: "User",
        roadmap_id: "BaseIdType",
    ) -> None:
        if user.is_superuser:
            return

        roadmap = await self.roadmap_repo.get_by_id(roadmap_id)
        if not roadmap:
            logger.error(
                "Roadmap(id=%r) not found",
                roadmap_id,
            )
            raise ValueError("NOT_FOUND")

        if roadmap.user_id == user.id:
            return

        logger.error(
            "Access denied to Roadmap(id=%r) for User(id=%r)",
            roadmap.id,
            user.id,
        )
        raise PermissionError("Forbidden")

    async def filter_blocks_for_user(
        self,
        user: "User",
        filters: dict,
    ) -> dict:
        if user.is_superuser:
            return filters

        allowed_roadmaps = await self.roadmap_repo.get_by_filters({"user_id": user.id})
        allowed_roadmaps_ids = [rm.id for rm in allowed_roadmaps]

        if not filters.get("roadmap_id"):
            filters["roadmap_id"] = allowed_roadmaps_ids
            return filters

        if filters.get("roadmap_id") in allowed_roadmaps_ids:
            return filters

        logger.error(
            "Access denied to Blocks with filters(%r) for User(id=%r)",
            filters,
            user.id,
        )
        raise PermissionError("Forbidden")

    async def ensure_can_view_block(
        self,
        user: "User",
        block: dict,
    ) -> None:

        await self.ensure_can_view_roadmap_by_id(user, block.get("roadmap_id"))

    async def ensure_can_view_block_by_id(
        self,
        user: "User",
        block_id: "BaseIdType",
    ) -> None:

        block = await self.block_repo.get_by_id(block_id)
        if not block:
            logger.error(
                "Block(id=%r) not found",
                block_id,
            )
            raise ValueError("NOT_FOUND")

        validated_block = await block_orm_to_model(block)

        await self.ensure_can_view_block(user, validated_block.model_dump())

    async def filter_cards_for_user(
        self,
        user: "User",
        filters: dict,
    ) -> dict:

        if user.is_superuser:
            return filters

        allowed_roadmaps = await self.roadmap_repo.get_by_filters({"user_id": user.id})
        allowed_roadmaps_ids = [r.id for r in allowed_roadmaps]

        allowed_blocks = await self.block_repo.get_by_filters(
            {"roadmap_id": allowed_roadmaps_ids}
        )
        allowed_blocks_ids = [b.id for b in allowed_blocks]

        if not filters.get("block_id"):
            filters["block_id"] = allowed_blocks_ids
            return filters

        if filters.get("block_id") in allowed_blocks_ids:
            return filters

        logger.error(
            "Access denied to Cards with filters(%r) for User(id=%r)",
            filters,
            user.id,
        )
        raise PermissionError("Forbidden")

    async def ensure_can_view_card(
        self,
        user: "User",
        card: dict,
    ) -> None:

        await self.ensure_can_view_block_by_id(user, card.get("block_id"))

    @staticmethod
    async def filter_sessions_for_user(
        user: "User",
        filters: dict,
    ) -> dict:
        logger.info("filters = %r", filters)
        if user.is_superuser:
            return filters

        if not filters.get("user_id"):
            filters["user_id"] = user.id
            return filters

        if filters.get("user_id") == user.id:
            return filters

        logger.error(
            "Access denied to Sessions with filters(%r) for User(id=%r)",
            filters,
            user.id,
        )
        raise PermissionError("Forbidden")

    @staticmethod
    async def ensure_can_view_session(
        user: "User",
        session: dict,
    ) -> None:

        if user.is_superuser or user.id == session.get("user_id"):
            return

        logger.error(
            "Access denied to Session(id=%r) for User(id=%r)",
            session.get("user_id"),
            user.id,
        )
        raise PermissionError("Forbidden")

    async def get_cards_for_session(
        self, user: "User", filters: dict
    ) -> list["BaseIdType"]:
        allowed_filters = await self.filter_cards_for_user(user, filters.copy())

        cards = await self.card_repo.get_by_filters(allowed_filters)
        if cards:
            cards_ids_queue = [c.id for c in cards]
            return cards_ids_queue

        logger.error(
            "No accessible cards found for user(id=%r) with filters(%r)",
            user.id,
            allowed_filters,
        )
        raise ValueError("NOT_FOUND")
