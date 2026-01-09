from typing import TYPE_CHECKING
from sqlalchemy import (
    select,
    insert,
    update,
    delete,
    func,
)

from app.core.dependencies import transaction_manager
from app.core.handlers import repository_handler
from app.models.session import Session
from app.repositories import BaseRepository
from app.schemas.session import (
    SessionStatus,
)

if TYPE_CHECKING:
    from app.core.types import BaseIdType


class SessionRepository(BaseRepository):
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
        filters: dict,
    ) -> list[Session]:
        stmt = select(Session)
        for field_name, value in filters.items():
            if value is not None:
                column = getattr(Session, field_name, None)
                if column is not None:
                    stmt = stmt.where(column == value)
        result = await self.session.execute(stmt)
        sessions = list(result.scalars().all())
        return sessions

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
    async def update(
        self,
        object_id: "BaseIdType",
        update_data: dict,
    ) -> Session | None:
        async with transaction_manager(self.session):
            stmt = (
                update(Session)
                .where(Session.id == object_id)
                .values(**update_data)
                .returning(Session)
            )
            result = await self.session.execute(stmt)
            roadmap = result.scalar_one_or_none()
            return roadmap

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
