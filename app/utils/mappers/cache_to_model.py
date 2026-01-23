import json

from app.schemas.user import UserRead
from app.schemas.roadmap import RoadmapRead


async def users_cache_to_model(cache: str) -> list[UserRead]:
    return [UserRead.model_validate_json(u) for u in json.loads(cache)]


async def cache_to_models(
    cached: str,
) -> list[RoadmapRead]:
    data_list = json.loads(cached)
    return [RoadmapRead.model_validate(data) for data in data_list]
