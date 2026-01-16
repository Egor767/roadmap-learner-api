import uuid

from app.core.custom_types import BaseIdType


async def generate_base_id() -> BaseIdType:
    return uuid.uuid4()
