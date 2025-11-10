from fastapi import APIRouter

from .endpoints.user import router as user_router
from .endpoints.roadmap import router as roadmap_router
from .endpoints.block import (
    router as block_router,
    resource_router as block_resource_router,
)
from .endpoints.card import (
    router as card_router,
    resource_router as card_resource_router,
)
from .endpoints.session_manager import router as session_manager_router

main_router = APIRouter()

main_router.include_router(user_router)
main_router.include_router(roadmap_router)
main_router.include_router(block_router)
main_router.include_router(block_resource_router)
main_router.include_router(card_router)
main_router.include_router(card_resource_router)
main_router.include_router(session_manager_router)
