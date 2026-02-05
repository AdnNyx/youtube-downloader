from pydantic import BaseModel, HttpUrl
from typing import Optional, Literal


class CreateJobRequest(BaseModel):
    url: HttpUrl
    type: Literal["mp4", "mp3"]
    quality: Optional[str] = None   # contoh: "720p"
    bitrate: Optional[int] = None   # contoh: 128, 192, 320


class JobStatusResponse(BaseModel):
    jobId: str
    status: str
    progress: int
    stage: str
    downloadUrl: Optional[str] = None
    filename: Optional[str] = None
    error: Optional[str] = None
