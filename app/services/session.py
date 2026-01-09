import random
from typing import TYPE_CHECKING

from app.core.handlers import service_handler
from app.core.logging import session_manager_service_logger as logger
from app.shared.generate_id import generate_base_id
from app.utils.mappers.orm_to_models import session_orm_to_model
from app.schemas.session import SessionMode

if TYPE_CHECKING:
    from app.core.types import BaseIdType
    from app.services import AccessService
    from app.repositories import SessionRepository
    from app.schemas.session import (
        SessionRead,
        SessionCreate,
        SessionFilters,
        SessionUpdate,
    )
    from app.models import User


class SessionService:
    def __init__(
        self,
        repo: "SessionRepository",
        access_service: "AccessService",
    ):
        self.repo = repo
        self.access = access_service

    @service_handler
    async def get_all(self) -> list["SessionRead"]:
        db_sessions = await self.repo.get_all()
        if not db_sessions:
            logger.warning("Sessions not found in DB")
            return []

        validated_sessions = [
            await session_orm_to_model(db_session) for db_session in db_sessions
        ]

        return validated_sessions

    @service_handler
    async def get_by_filters(
        self,
        current_user: "User",
        filters: "SessionFilters",
    ) -> list["SessionRead"]:
        filters_dict = filters.model_dump()
        accessed_filters = await self.access.filter_sessions_for_user(
            current_user,
            filters_dict,
        )

        db_sessions = await self.repo.get_by_filters(accessed_filters)
        if not db_sessions:
            logger.warning(
                "Sessions with filters(%r) not found",
                filters,
            )
            return []

        validated_sessions = [
            await session_orm_to_model(db_session) for db_session in db_sessions
        ]

        return validated_sessions

    @service_handler
    async def get_by_id(
        self,
        current_user: "User",
        session_id: "BaseIdType",
    ) -> "SessionRead":
        db_session = await self.repo.get_by_id(session_id)
        if not db_session:
            logger.error("Session(id=%r) not found", session_id)
            raise ValueError("NOT_FOUND")

        validated_session = await session_orm_to_model(db_session)
        await self.access.ensure_can_view_session(
            current_user, validated_session.model_dump()
        )

        return validated_session

    @service_handler
    async def get_next_card_id(
        self,
        current_user: "User",
        session_id: "BaseIdType",
    ) -> "BaseIdType":
        session = await self.get_by_id(current_user, session_id)

        try:
            next_card_id = session.card_ids_queue[session.current_card_index]
        except (IndexError, TypeError, AttributeError) as e:
            logger.warning(
                "Next card access failed for session %r: queue=%r, index=%r, error=%r",
                session_id,
                getattr(session, "card_ids_queue", None),
                getattr(session, "current_card_index", None),
                e,
            )
            raise ValueError("Next card id not found or invalid session state") from e

        await self.repo.update(
            session.id,
            {"current_card_index": session.current_card_index + 1},
        )

        return next_card_id

    @service_handler
    async def create(
        self,
        current_user: "User",
        session_create_data: "SessionCreate",
    ) -> "SessionRead":
        filters = session_create_data.model_dump(
            exclude={"mode", "mix"}, exclude_none=True
        )
        if session_create_data.mode is SessionMode.REVIEW:
            filters["status"] = "review"

        cards_ids_queue = await self.access.get_cards_for_session(
            current_user,
            filters,
        )
        logger.info("cards ids queue: %r", cards_ids_queue)

        session_dict = session_create_data.model_dump(exclude={"mix"})
        session_dict["user_id"] = current_user.id
        session_dict["id"] = await generate_base_id()
        if session_create_data.mix:
            random.shuffle(cards_ids_queue)
        session_dict["card_ids_queue"] = cards_ids_queue

        created_session = await self.repo.create(session_dict)
        if not created_session:
            logger.error(
                "Session with params(%r) for User(id=%r) not created",
                created_session,
                current_user.id,
            )
            raise ValueError("OPERATION_FAILED")

        validated_created_session = await session_orm_to_model(created_session)

        return validated_created_session

    @service_handler
    async def delete(
        self,
        current_user: "User",
        session_id: "BaseIdType",
    ) -> None:
        await self.get_by_id(current_user, session_id)

        success = await self.repo.delete(session_id)
        if success:
            logger.info("Session(id=%r) was deleted successfully", session_id)
        else:
            logger.error("Failed to delete Session(id=%r)", session_id)
            raise ValueError("OPERATION_FAILED")

    @service_handler
    async def update(
        self,
        current_user: "User",
        session_id: "BaseIdType",
        session_update_data: "SessionUpdate",
    ) -> "SessionRead":
        await self.get_by_id(current_user, session_id)

        session_dict = session_update_data.model_dump(exclude_unset=True)

        updated_session = await self.repo.update(session_id, session_dict)
        if not updated_session:
            logger.error("Failed to update Session(id=%r)", session_id)
            raise ValueError("OPERATION_FAILED")

        validated_updated_session = await session_orm_to_model(updated_session)

        return validated_updated_session
