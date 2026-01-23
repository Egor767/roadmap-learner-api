import hashlib
import json
import logging
from functools import wraps
from typing import Callable, Any, Tuple, Dict, Optional

logger = logging.getLogger("CACHE-LOGGER")


async def key_builder(
    func: Callable[..., Any],
    namespace: str,
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
    exclude_types: tuple = (),
) -> str:
    cache_kw = {}
    for name, value in kwargs.items():
        if isinstance(value, exclude_types):
            continue
        cache_kw[name] = value

    cache_key = hashlib.md5(
        f"{func.__module__}:{func.__name__}:{args}:{cache_kw}".encode()
    ).hexdigest()
    return f"{namespace}:{cache_key}"


def cached(
    redis: any,
    ttl: int = 300,
    namespace: str = "cache",
    key_maker: Optional[Callable] = None,
    cache_empty: bool = True,
):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, *args, **kwargs) -> Any:
            # Автоматический ключ
            func_key = f"{func.__module__}.{func.__name__}"
            key_args = hash((args, frozenset(kwargs.items())))
            cache_key = f"{namespace}:{func_key}:{key_args}"

            cached_data = await redis.get(cache_key)
            if cached_data:
                logger.info("Cache HIT: %s", cache_key)
                return json.loads(cached_data)

            result = await func(self, *args, **kwargs)

            if cache_empty or result:
                await redis.set(cache_key, json.dumps(result), ex=ttl)
                logger.info("Cache SET: %s", cache_key)

            return result

        return wrapper

    return decorator
