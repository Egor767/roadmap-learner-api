import json

from app.schemas.block import BlockRead
from app.schemas.user import UserRead
from app.schemas.roadmap import RoadmapRead
from app.schemas.card import CardRead


async def users_cache_to_model(cache: str) -> list[UserRead]:
    return [UserRead.model_validate_json(u) for u in json.loads(cache)]


async def roadmap_cache_to_models(
    cached: str,
) -> list[RoadmapRead]:
    data_list = json.loads(cached)
    return [RoadmapRead.model_validate(data) for data in data_list]


async def block_cache_to_models(
    cached: str,
) -> list[BlockRead]:
    data_list = json.loads(cached)
    return [BlockRead.model_validate(data) for data in data_list]


async def card_cache_to_models(
    cached: str,
) -> list[CardRead]:
    data_list = json.loads(cached)
    return [CardRead.model_validate(data) for data in data_list]
