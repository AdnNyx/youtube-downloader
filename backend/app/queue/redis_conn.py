import redis
from app.core.config import settings

def get_redis():
    return redis.Redis.from_url(settings.REDIS_URL)
