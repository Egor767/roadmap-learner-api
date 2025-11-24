import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models import User
    from app.schemas.user import UserRead
    from app.schemas.roadmap import RoadmapRead
    from app.repositories import RoadmapRepository
    from app.schemas.block import BlockRead


logger = logging.getLogger("AccessService-Logger")


class AccessService:
    def __init__(self, roadmap_repo: "RoadmapRepository"):
        self.roadmap_repo = roadmap_repo

    @staticmethod
    async def filter_users_for_user(
        user: "User",
        users: list["UserRead"],
    ) -> list["UserRead"]:

        if user.is_superuser:
            return users

        return [u for u in users if u.id == user.id]

    @staticmethod
    async def filter_roadmaps_for_user(
        user: "User",
        roadmaps: list["RoadmapRead"],
    ) -> list["RoadmapRead"]:

        if user.is_superuser:
            return roadmaps

        return [r for r in roadmaps if r.user_id == user.id]

    @staticmethod
    async def ensure_can_view_roadmap(
        user: "User",
        roadmap: "RoadmapRead",
    ) -> None:

        if user.is_superuser or user.id == roadmap.user_id:
            return

        logger.error(
            "Access denied to Roadmap(id=%r) for User(id=%r)",
            roadmap.id,
            user.id,
        )
        raise PermissionError("Forbidden")

    async def filter_blocks_for_user(
        self,
        user: "User",
        blocks: list["BlockRead"],
    ) -> list["BlockRead"]:

        if user.is_superuser:
            return blocks

        allowed_roadmaps = await self.roadmap_repo.get_by_filters(dict())
        allowed_roadmaps_owned = [
            rm for rm in allowed_roadmaps if rm.user_id == user.id
        ]
        allowed_ids = {rm.id for rm in allowed_roadmaps_owned}

        return [b for b in blocks if b.roadmap_id in allowed_ids]

    async def ensure_can_view_block(
        self,
        user: "User",
        block: "BlockRead",
    ) -> None:

        if user.is_superuser:
            return

        target_roadmap = await self.roadmap_repo.get_by_id(block.roadmap_id)

        if target_roadmap and target_roadmap.user_id == user.id:
            return

        logger.error(
            "Access denied to Block(id=%r) for User(id=%r)",
            block.id,
            user.id,
        )
        raise PermissionError("Forbidden")
