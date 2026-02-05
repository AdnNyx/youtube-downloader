from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any


class ParseRequest(BaseModel):
    url: HttpUrl


class VideoFormat(BaseModel):
    label: str
    itag: Optional[int] = None
    ext: Optional[str] = None
    hasAudio: Optional[bool] = None
    vcodec: Optional[str] = None
    acodec: Optional[str] = None
    filesize: Optional[int] = None


class ParseResponse(BaseModel):
    id: str
    title: str
    channel: Optional[str] = None
    duration: Optional[int] = None
    thumbnail: Optional[str] = None
    formats: Dict[str, List[VideoFormat]]
    raw: Optional[Dict[str, Any]] = None  # opsional untuk debug (nanti bisa dimatikan)
