from typing import TYPE_CHECKING

from app.core.handlers import service_handler
from app.core.logging import session_manager_service_logger as logger
from app.shared.generate_id import generate_base_id
from app.utils.mappers.orm_to_models import session_orm_to_model
from app.external.card_service import get_card_from_service
from app.external.session_manager_service import calculate_session_stats

if TYPE_CHECKING:
    from app.core.types import BaseIdType
    from app.services import AccessService
    from app.repositories import SessionManagerRepository
    from app.schemas.card import CardRead
    from app.schemas.session import (
        SessionRead,
        SessionCreate,
        SessionFilters,
        SessionResult,
        SubmitAnswerRequest,
    )
    from app.models import User


class SessionManagerService:
    def __init__(
        self,
        repo: "SessionManagerRepository",
        access_service: "AccessService",
    ):
        self.repo = repo
        self.access = access_service

    @service_handler
    async def get_all(self) -> list["SessionRead"]:
        db_sessions = await self.repo.get_all()
        logger.info(
            "Successful get all sessions, count: %r",
            len(db_sessions),
        )

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
    ) -> SessionRead:
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
    async def create(
        self,
        current_user: "User",
        session_create_data: "SessionCreate",
    ) -> "SessionRead":
        session_dict = session_create_data.model_dump()
        del session_dict["settings"]
        session_dict["user_id"] = current_user.id
        session_dict["id"] = generate_base_id()

        created_session = await self.repo.create(session_dict)
        if not created_session:
            logger.error(
                "Session with params(%r) for User(id=%r) not created",
                created_session,
                current_user.id,
            )
            raise ValueError("OPERATION_FAILED")

        validated_created_roadmap = await session_orm_to_model(created_session)

        return validated_created_roadmap

    @service_handler
    async def get_next_card(
        self,
        user_id: BaseIdType,
        session_id: BaseIdType,
    ) -> CardRead:
        next_card_id = await self.repo.get_next_card_id(user_id, session_id)

        if not next_card_id:
            logger.warning("Next card not found for session: %r", session_id)
            raise ValueError("Next card not found")

        card_data = await get_card_from_service(str(user_id), str(next_card_id))
        if not card_data:
            raise ValueError("Card not found")

        return CardRead.model_validate(card_data)

    @service_handler
    async def delete_session(
        self,
        current_user: "User",
        session_id: "BaseIdType",
    ) -> None:

        success = await self.repo.delete(session_id)
        if success:
            logger.info("Session(id=%r) was deleted successfully", session_id)
        else:
            logger.error("Failed to delete Session(id=%r)", session_id)
            raise ValueError("OPERATION_FAILED")

    @service_handler
    async def finish_session(
        self, user_id: BaseIdType, session_id: BaseIdType
    ) -> SessionResult:
        finished_session = await self.repo.finish_session(user_id, session_id)

        if not finished_session:
            logger.warning("Session not found for finish: %r", session_id)
            raise ValueError("Session not found")

        result_data = {
            **finished_session.model_dump(),
            **calculate_session_stats(finished_session),
        }

        logger.info("Successful finishing session: %r", session_id)
        return SessionResult.model_validate(result_data)

    @service_handler
    async def abandon_session(
        self, user_id: BaseIdType, session_id: BaseIdType
    ) -> bool:
        success = await self.repo.abandon_session(user_id, session_id)

        if success:
            logger.info("Session abandoned successfully: %r", session_id)
        else:
            logger.warning(
                "Failed to abandon session: %r - session not found, not active, or not owned by user",
                session_id,
            )

        return success

    @service_handler
    async def submit_answer(
        self,
        user_id: BaseIdType,
        session_id: BaseIdType,
        answer_data: SubmitAnswerRequest,
    ) -> SessionRead:
        # need ro check if session exist, status==active, if mode==exam then answer_data.answer!=review
        # answer_data.card_id in Session.card_queue

        updated_session = await self.repo.submit_answer(
            user_id, session_id, answer_data
        )

        if not updated_session:
            logger.warning("Failed to update session: %r", session_id)
            raise ValueError("Failed to update session")

        return SessionRead.model_validate(updated_session)
