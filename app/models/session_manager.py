from datetime import datetime

from sqlalchemy import DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .mixins import (
    TimestampMixin,
    UserRelationMixin,
    RoadmapRelationMixin,
    BlockRelationMixin,
    IdMixin,
)


class Session(
    IdMixin,
    TimestampMixin,
    UserRelationMixin,
    RoadmapRelationMixin,
    BlockRelationMixin,
    Base,
):
    # _user_back_populates = "sessions"
    # _roadmap_back_populates = None
    # _block_back_populates = None
    # _block_id_nullable = True

    mode: Mapped[str] = mapped_column(
        SQLEnum(
            "review",
            "exam",
            name="session_mode",
        ),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        SQLEnum(
            "active",
            "completed",
            "abandoned",
            name="session_status",
        ),
        default="active",
    )

    card_queue: Mapped[list | None] = mapped_column(
        JSONB,
        default=list,
        nullable=True,
    )

    current_card_index: Mapped[int] = mapped_column(
        default=0,
    )

    correct_answers: Mapped[int] = mapped_column(
        default=0,
    )

    incorrect_answers: Mapped[int] = mapped_column(
        default=0,
    )

    review_answers: Mapped[int] = mapped_column(
        default=0,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __str__(self):
        return (
            f"{self.__class__.__name__}(id={self.id}, "
            f"user_id={self.user_id!r}), "
            f"mode={self.mode}, "
            f"status={self.status}"
        )

    def __repr__(self):
        return str(self)
