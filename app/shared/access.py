import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models import User

logger = logging.getLogger("Access-Logger")


def get_accessed_filters(
    user: "User",
    filters: dict,
) -> dict:
    accessed_filters = filters.copy()
    if user.is_superuser:
        return accessed_filters

    if not accessed_filters.get("user_id"):
        accessed_filters["user_id"] = user.id
        return accessed_filters

    if accessed_filters.get("user_id") == user.id:
        return accessed_filters

    logger.error(
        "Access denied to Roadmaps with filters(%r) for User(id=%r)",
        filters,
        user.id,
    )
    raise PermissionError("Forbidden")


def user_can_read_entity(
    user: "User",
    entity: dict,
) -> None:

    if user.is_superuser or user.id == entity.get("user_id"):
        return

    logger.error(
        "Access denied to Entity(id=%r) for User(id=%r)",
        entity.get("user_id"),
        user.id,
    )
    raise PermissionError("Forbidden")
