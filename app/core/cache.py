import redis
from app.core.config import settings

try:
    redis_client = redis.from_url(settings.REDIS_URL)
    redis_available = True
except redis.ConnectionError:
    redis_client = None
    redis_available = False


def get_cached_result(key: str):
    if not redis_available:
        return None
    try:
        return redis_client.get(key)
    except redis.ConnectionError:
        return None


def set_cached_result(key: str, value: str, expire: int = 3600):
    if not redis_available:
        return
    try:
        redis_client.setex(key, expire, value)
    except redis.ConnectionError:
        pass