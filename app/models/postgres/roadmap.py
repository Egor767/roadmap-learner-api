from datetime import datetime

from sqlalchemy import String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.sql import func

from .base import Base
from .mixins import UserRelationMixin


class Roadmap(UserRelationMixin, Base):
    _user_back_populates = "roadmaps"

    title: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(
        SQLEnum("draft", "active", "archived", name="roadmap_status"), default="draft"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        default=func.now(),
        server_default=func.now(),
    )

    def __str__(self):
        return f"{self.__class__.__name__}(id={self.id}, title={self.title!r}), status={self.status}"

    def __repr__(self):
        return str(self)
