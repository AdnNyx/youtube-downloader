from fastapi import APIRouter
from app.queue.redis_conn import get_redis
from app.queue.rq_queue import get_queue

router = APIRouter()

@router.get("/ping")
def ping_redis():
    r = get_redis()
    return {"success": True, "redis_ping": r.ping()}

@router.get("/info")
def queue_info():
    q = get_queue()
    return {
        "success": True,
        "queue": q.name,
        "count": q.count
    }
