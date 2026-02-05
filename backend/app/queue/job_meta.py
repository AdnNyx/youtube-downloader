import json
from typing import Any, Dict, Optional
from app.queue.redis_conn import get_redis

def job_meta_key(job_id: str) -> str:
    return f"job:{job_id}:meta"

def set_job_meta(job_id: str, data: Dict[str, Any], ttl_seconds: int = 3600):
    r = get_redis()
    key = job_meta_key(job_id)
    r.set(key, json.dumps(data))
    r.expire(key, ttl_seconds)

def get_job_meta(job_id: str) -> Optional[Dict[str, Any]]:
    r = get_redis()
    key = job_meta_key(job_id)
    raw = r.get(key)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None
