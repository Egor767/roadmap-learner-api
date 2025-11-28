import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, ConfigDict

from app.core.types import BaseIdType
from app.schemas.card import CardStatus


class BaseSession(BaseModel):
    roadmap_id: BaseIdType


class SessionMode(str, Enum):
    REVIEW = "review"
    EXAM = "exam"


class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class SessionCreate(BaseSession):
    block_id: BaseIdType | None = None
    mode: SessionMode


class SessionUpdate(BaseModel):
    status: SessionStatus | None = None
    current_card_index: int | None = None
    correct_answers: int | None = None
    incorrect_answers: int | None = None
    review_answers: int | None = None


class SessionRead(BaseSession):
    id: BaseIdType
    user_id: BaseIdType
    block_id: BaseIdType | None = None

    mode: SessionMode

    status: SessionStatus
    card_queue: list[BaseIdType] = []
    current_card_index: int

    correct_answers: int
    incorrect_answers: int
    review_answers: int

    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class SessionFilters(BaseModel):
    user_id: BaseIdType | None = None
    roadmap_id: BaseIdType | None = None
    block_id: BaseIdType | None = None
    mode: SessionMode | None = None
    status: SessionStatus | None = None


class SessionResult(BaseModel):
    id: BaseIdType
    user_id: BaseIdType
    roadmap_id: BaseIdType
    mode: SessionMode
    total_cards: int
    correct_answers: int
    incorrect_answers: int
    review_answers: int
    accuracy_percentage: float
    completed_at: datetime


class SubmitAnswerRequest(BaseModel):
    card_id: BaseIdType
    answer: CardStatus
