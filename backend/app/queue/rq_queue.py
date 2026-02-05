from rq import Queue
from app.queue.redis_conn import get_redis

def get_queue(name: str = "default") -> Queue:
    redis_conn = get_redis()
    return Queue(name, connection=redis_conn)
