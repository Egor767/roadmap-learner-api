from typing import TYPE_CHECKING

from app.core.handlers import service_handler
from app.core.logging import card_service_logger as logger
from app.shared.generate_id import generate_base_id

if TYPE_CHECKING:
    from app.core.types import BaseIdType
    from app.services import AccessService
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
        access_service: "AccessService",
    ):
        self.repo = repo
        self.access = access_service

    @service_handler
    async def get_all_cards(self) -> list["CardRead"] | list[None]:
        cards = await self.repo.get_all()
        if not cards:
            logger.warning("Cards not found in DB")
            return []

        return cards

    @service_handler
    async def get_cards_by_filters(
        self,
        current_user: "User",
        filters: "CardFilters",
    ) -> list["CardRead"] | list[None]:
        filters_dict = filters.model_dump()
        accessed_filters = await self.access.filter_cards_for_user(
            current_user,
            filters_dict,
        )

        cards = await self.repo.get_by_filters(accessed_filters)
        if not cards:
            logger.warning("Cards with filters(%r) not found", filters)
            return []

        return cards

    @service_handler
    async def get_card_by_id(
        self,
        current_user: "User",
        card_id: "BaseIdType",
    ) -> "CardRead":
        card = await self.repo.get_by_id(card_id)
        if not card:
            logger.error(f"Card(%r) not found or access denied", card_id)
            raise ValueError("NOT_FOUND")

        await self.access.ensure_can_view_card(current_user, card.model_dump())

        return card

    @service_handler
    async def create_card(
        self,
        current_user: "User",
        card_create_data: "CardCreate",
    ) -> "CardRead":
        card_dict = card_create_data.model_dump()
        card_dict["id"] = await generate_base_id()

        await self.access.ensure_can_view_card(current_user, card_dict)

        created_card = await self.repo.create(card_dict)
        if not created_card:
            logger.error(
                "Card with params(%r) for User(id=%r) not created",
                card_create_data,
                current_user.id,
            )
            raise ValueError("OPERATION_FAILED")

        return created_card

    @service_handler
    async def delete_card(
        self,
        current_user: "User",
        card_id: "BaseIdType",
    ) -> None:
        await self.get_card_by_id(current_user, card_id)

        success = await self.repo.delete(card_id)
        if success:
            logger.info("Card deleted successfully: %r", card_id)
        else:
            logger.error("Deletion for Card(%r) FAILED", card_id)
            raise ValueError("OPERATION_FAILED")

    @service_handler
    async def update_card(
        self,
        current_user: "User",
        card_id: "BaseIdType",
        card_update_data: "CardUpdate",
    ) -> "CardRead":
        await self.get_card_by_id(current_user, card_id)

        card_dict = card_update_data.model_dump(exclude_unset=True)

        updated_card = await self.repo.update(card_id, card_dict)
        if not updated_card:
            logger.warning("Failed to update Block(id=%r)", card_id)
            raise ValueError("OPERATION_FAILED")

        return updated_card
