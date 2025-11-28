from typing import List, Optional

from sqlalchemy import select, insert, update, delete, func

from app.core.dependencies import transaction_manager
from app.core.handlers import repository_handler
from app.core.types import BaseIdType
from app.models.session_manager import Session
from app.repositories import BaseRepository
from app.schemas.card import CardStatus
from app.schemas.session import (
    SessionRead,
    SessionCreate,
    SessionFilters,
    SessionStatus,
    SubmitAnswerRequest,
)


class SessionManagerRepository(BaseRepository):
    @repository_handler
    async def get_all(self) -> list[Session]:
        stmt = select(Session)
        result = await self.session.execute(stmt)
        sessions = list(result.scalars().all())
        return sessions

    @repository_handler
    async def get_by_id(self, session_id: "BaseIdType") -> Session | None:
        stmt = select(Session).where(Session.id == session_id)
        result = await self.session.execute(stmt)
        session = result.scalar_one_or_none()
        return session

    @repository_handler
    async def get_by_filters(
        self,
        user_id: "BaseIdType",
        filters: dict,
    ) -> list[Session]:
        stmt = select(Session).where(Session.user_id == user_id)
        for field_name, value in filters.items():
            if value is not None:
                column = getattr(Session, field_name, None)
                if column is not None:
                    stmt = stmt.where(column == value)
        result = await self.session.execute(stmt)
        sessions = list(result.scalars().all())
        return sessions

    @repository_handler
    async def get_next_card_id(self, session_id: "BaseIdType") -> "BaseIdType" | None:
        stmt = select(Session).where(Session.id == session_id)
        result = await self.session.execute(stmt)
        session = result.scalar_one_or_none()
        next_card_id = session.card_queue[session.current_card_index]
        if next_card_id:
            return next_card_id
        return

    @repository_handler
    async def create(self, session_create_data: dict) -> Session | None:
        async with transaction_manager(self.session):
            stmt = insert(Session).values(**session_create_data).returning(Session)
            result = await self.session.execute(stmt)
            session = result.scalar_one_or_none()
            return session

    @repository_handler
    async def delete(self, session_id: "BaseIdType") -> bool:
        async with transaction_manager(self.session):
            stmt = delete(Session).where(Session.id == session_id)
            result = await self.session.execute(stmt)
            return result.rowcount > 0

    @repository_handler
    async def finish_session(self, session_id: "BaseIdType") -> Session:
        async with transaction_manager(self.session):
            stmt = (
                update(Session)
                .where(
                    Session.id == session_id,
                    Session.status == SessionStatus.ACTIVE,
                )
                .values(status=SessionStatus.COMPLETED, completed_at=func.now())
                .returning(Session)
            )
            result = await self.session.execute(stmt)
            session = result.scalar_one_or_none()
            return session

    @repository_handler
    async def abandon_session(self, session_id: "BaseIdType") -> bool:
        async with transaction_manager(self.session):
            stmt = (
                update(Session)
                .where(
                    Session.id == session_id,
                    Session.status == SessionStatus.ACTIVE,
                )
                .values(status=SessionStatus.ABANDONED, completed_at=func.now())
            )
            result = await self.session.execute(stmt)
            return result.rowcount > 0

    @repository_handler
    async def submit_answer(
        self,
        session_id: "BaseIdType",
        answer_data: SubmitAnswerRequest,
    ) -> Session:
        async with transaction_manager(self.session):
            stmt = select(Session).where(Session.id == session_id)
            result = await self.session.execute(stmt)
            session = result.scalar_one_or_none()

            update_data = {}

            if answer_data.answer == CardStatus.KNOWN:
                update_data["correct_answers"] = session.correct_answers + 1
            elif answer_data.answer == CardStatus.UNKNOWN:
                update_data["incorrect_answers"] = session.incorrect_answers + 1
            elif answer_data.answer == CardStatus.REVIEW:
                update_data["review_answers"] = session.review_answers + 1

            update_data["current_card_index"] = session.current_card_index + 1

            stmt = (
                update(Session)
                .where(Session.id == session_id)
                .values(**update_data)
                .returning(Session)
            )

            result = await self.session.execute(stmt)
            updated_session = result.scalar_one_or_none()
            return updated_session
