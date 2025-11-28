from typing import Annotated, TYPE_CHECKING

from fastapi import APIRouter, Depends
from starlette import status

from app.core.authentication.fastapi_users import current_active_user
from app.core.config import settings
from app.core.dependencies.services import get_session_manager_service
from app.core.handlers import router_handler
from app.core.types import BaseIdType
from app.schemas.card import CardRead
from app.schemas.session import (
    SessionRead,
    SessionFilters,
    SessionCreate,
    SessionResult,
    SubmitAnswerRequest,
)

if TYPE_CHECKING:
    from app.services import SessionManagerService
    from app.models import User


router = APIRouter(
    prefix=settings.api.v1.sessions,
    tags=["Sessions"],
)


@router.get(
    "",
    name="sessions:all_sessions",
    response_model=list[SessionRead],
)
@router_handler
async def get_all_sessions(
    session_manager_service: Annotated[
        SessionManagerService,
        Depends(get_session_manager_service),
    ],
) -> list[SessionRead]:
    return await session_manager_service.get_all()


# -------------------------------------- GET ----------------------------------------------
@router.get(
    "/filters",
    name="sessions:filter_sessions",
    response_model=list[SessionRead],
)
async def get_sessions(
    filters: Annotated[
        SessionFilters,
        Depends(),
    ],
    current_user: Annotated[
        "User",
        Depends(current_active_user),
    ],
    session_manager_service: Annotated[
        SessionManagerService,
        Depends(get_session_manager_service),
    ],
) -> list[SessionRead]:
    return await session_manager_service.get_by_filters(
        current_user,
        filters,
    )


@router.get(
    "/{session_id}",
    name="sessions:session",
    response_model=SessionRead,
)
@router_handler
async def get_session(
    session_id: BaseIdType,
    current_user: Annotated[
        "User",
        Depends(current_active_user),
    ],
    session_manager_service: Annotated[
        SessionManagerService,
        Depends(get_session_manager_service),
    ],
) -> SessionRead:
    return await session_manager_service.get_by_id(
        current_user,
        session_id,
    )


@router.get(
    "/{session_id}/next-card",
    response_model=CardRead,
)
@router_handler
async def get_next_card(
    session_id: BaseIdType,
    current_user: Annotated[
        "User",
        Depends(current_active_user),
    ],
    session_manager_service: Annotated[
        SessionManagerService,
        Depends(get_session_manager_service),
    ],
):
    return await session_manager_service.get_next_card(
        current_user,
        session_id,
    )


# -------------------------------------- CREATE --------------------------------------
@router.post(
    "/",
    name="sessions:create_session",
    response_model=SessionRead,
)
@router_handler
async def create_session(
    session_create_data: SessionCreate,
    current_user: Annotated[
        "User",
        Depends(current_active_user),
    ],
    session_manager_service: Annotated[
        SessionManagerService,
        Depends(get_session_manager_service),
    ],
):
    return await session_manager_service.create(
        current_user,
        session_create_data,
    )


# -------------------------------------- DELETE --------------------------------------
@router.delete(
    "/{session_id}",
    name="sessions:delete_session",
    status_code=status.HTTP_204_NO_CONTENT,
)
@router_handler
async def delete_block(
    session_id: BaseIdType,
    current_user: Annotated[
        "User",
        Depends(current_active_user),
    ],
    session_manager_service: Annotated[
        SessionManagerService,
        Depends(get_session_manager_service),
    ],
) -> None:
    await session_manager_service.delete(
        current_user,
        session_id,
    )


# -------------------------------------- UPDATE --------------------------------------
@router.patch(
    "/{session_id}",
    name="sessions:patch_session",
    response_model=SessionRead,
)
@router_handler
async def abandon_session(
    session_id: BaseIdType,
    current_user: Annotated[
        "User",
        Depends(current_active_user),
    ],
    session_manager_service: Annotated[
        SessionManagerService,
        Depends(get_session_manager_service),
    ],
) -> SessionRead:
    return await session_manager_service.update(
        current_user,
        session_id,
    )


# submit answer
@router.patch(
    "/{session_id}/answer",
    response_model=SessionRead,
)
@router_handler
async def submit_answer(
    session_id: BaseIdType,
    answer_data: SubmitAnswerRequest,
    current_user: Annotated[
        "User",
        Depends(current_active_user),
    ],
    session_manager_service: Annotated[
        SessionManagerService,
        Depends(get_session_manager_service),
    ],
):
    return await session_manager_service.submit_answer(
        current_user,
        session_id,
        answer_data,
    )
