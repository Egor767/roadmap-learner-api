from app.core.handlers import logger
from app.models.session import Session
from app.schemas.block import BlockRead
from app.schemas.card import CardRead
from app.schemas.roadmap import RoadmapRead
from app.schemas.session import SessionRead
from app.schemas.user import UserRead
from app.models import (
    Roadmap,
    User,
    Block,
    Card,
)


async def user_orm_to_model(db_user: User | None) -> UserRead | None:
    if db_user:
        return UserRead.model_validate(db_user)
    return


async def roadmap_orm_to_model(db_roadmap: Roadmap | None) -> RoadmapRead | None:
    if db_roadmap:
        return RoadmapRead.model_validate(db_roadmap)
    return None


async def block_orm_to_model(db_block: Block | None) -> BlockRead | None:
    if db_block:
        return BlockRead.model_validate(db_block)
    return


async def card_orm_to_model(db_card: Card | None) -> CardRead | None:
    if db_card:
        return CardRead.model_validate(db_card)
    return


async def session_orm_to_model(db_session: Session | None) -> SessionRead | None:
    if db_session:
        return SessionRead.model_validate(db_session)
    return
