from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.queue import router as queue_router
from app.api.routes.youtube import router as youtube_router
from fastapi import APIRouter
from app.api.routes import youtube

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["Health"])
api_router.include_router(queue_router, prefix="/queue", tags=["Queue"])
api_router.include_router(youtube_router, prefix="/youtube", tags=["YouTube"])
api_router.include_router(youtube.router, prefix="/youtube", tags=["YouTube"])