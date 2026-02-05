import json
from redis import Redis
from app.config import REDIS_URL

def get_redis():
    return Redis.from_url(REDIS_URL, decode_responses=True)

def meta_key(job_id: str) -> str:
    return f"job:{job_id}:meta"

def set_meta(job_id: str, data: dict, ttl: int = 3600):
    r = get_redis()
    key = meta_key(job_id)
    r.set(key, json.dumps(data))
    r.expire(key, ttl)
