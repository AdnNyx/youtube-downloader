import os
import uuid

from fastapi.responses import FileResponse
from fastapi import APIRouter, HTTPException

from rq.job import Job

from app.schemas.youtube import ParseRequest
from app.services.youtube_service import parse_youtube
from app.utils.validators import is_allowed_youtube_url

from app.queue.rq_queue import get_queue
from app.queue.redis_conn import get_redis
from app.schemas.job import CreateJobRequest
from app.core.config import settings


router = APIRouter()


@router.post("/parse")
def parse(req: ParseRequest):
    url = str(req.url)

    if not is_allowed_youtube_url(url):
        raise HTTPException(status_code=400, detail="Only YouTube URLs are allowed")

    try:
        data = parse_youtube(url)
        return {"success": True, "message": "Video parsed", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse video: {str(e)}")


@router.post("/jobs")
def create_job(req: CreateJobRequest):
    url = str(req.url)

    if not is_allowed_youtube_url(url):
        raise HTTPException(status_code=400, detail="Only YouTube URLs are allowed")

    # default values
    if req.type == "mp4" and not req.quality:
        req.quality = "720p"

    if req.type == "mp3" and not req.bitrate:
        req.bitrate = 192

    q = get_queue("default")

    # folder id unik agar tidak tabrakan
    folder_id = uuid.uuid4().hex

    job = q.enqueue(
        "app.jobs.youtube_job.download_job",
        url,
        folder_id,
        req.type,
        req.quality,
        req.bitrate,
        settings.STORAGE_DIR,
    )

    return {
        "success": True,
        "message": "Job created",
        "data": {"jobId": job.id, "status": "queued"},
    }


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    redis_conn = get_redis()

    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")

    status = job.get_status()  # queued/started/finished/failed
    result = job.result if job.is_finished else None
    error = str(job.exc_info) if job.is_failed else None

    # ambil progress & stage dari meta (INILAH FIX 0%)
    meta_progress = job.meta.get("progress", 0)
    meta_stage = job.meta.get("stage", status)

    download_url = f"/api/youtube/download/{job_id}" if job.is_finished else None

    response = {
        "jobId": job_id,
        "status": status,
        "progress": meta_progress,
        "stage": meta_stage,
        "filename": result.get("file_name") if result else None,
        "downloadUrl": download_url,
        "error": error,
    }

    return {"success": True, "message": "Job status", "data": response}


@router.get("/download/{job_id}")
def download(job_id: str):
    redis_conn = get_redis()

    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")

    if not job.is_finished:
        raise HTTPException(status_code=409, detail="Job not finished yet")

    result = job.result

    # FIX: key yang benar adalah file_path
    if not result or "file_path" not in result:
        raise HTTPException(status_code=500, detail="Output file not found")

    path = result["file_path"]
    filename = result.get("file_name", os.path.basename(path))

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File missing")

    return FileResponse(path, filename=filename)
