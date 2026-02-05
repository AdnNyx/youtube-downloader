import os
from app.core.config import settings


def ensure_job_dir(job_id: str) -> str:
    job_dir = os.path.join(settings.STORAGE_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    return job_dir


def get_output_file_path(job_id: str, filename: str) -> str:
    job_dir = ensure_job_dir(job_id)
    return os.path.join(job_dir, filename)
