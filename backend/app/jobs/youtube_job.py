import shutil
import subprocess
from pathlib import Path
from typing import Optional, Literal

from rq import get_current_job


def _ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _which_ffmpeg() -> str:
    """
    Cari ffmpeg.
    - kalau sudah ada di PATH -> return path ffmpeg
    - kalau tidak, fallback ke bin/ffmpeg.exe (opsional)
    """
    ff = shutil.which("ffmpeg")
    if ff:
        return ff

    # fallback optional (kalau kamu simpan ffmpeg di project)
    local = Path(__file__).resolve().parent.parent.parent / "bin" / "ffmpeg.exe"
    if local.exists():
        return str(local)

    raise RuntimeError("FFmpeg tidak ditemukan. Install ffmpeg dan pastikan ada di PATH.")


def _progress(pct: int, stage: str = "processing"):
    """
    Simpan progress ke Redis (job.meta)
    """
    job = get_current_job()
    if not job:
        return

    job.meta["progress"] = max(0, min(100, int(pct)))
    job.meta["stage"] = stage
    job.save_meta()


def download_job(
    url: str,
    job_id: str,
    file_type: Literal["mp4", "mp3"],
    quality: Optional[str] = None,
    bitrate: Optional[int] = None,
    storage_dir: str = "storage",
):
    """
    Download YouTube video/audio using yt-dlp.
    Progress saved to job.meta.

    Returns dict:
        {
          "job_id": "...",
          "type": "mp4/mp3",
          "file_name": "...",
          "file_path": "...",
          "download_url": "/api/youtube/download/{job_id}",
          "status": "finished"
        }
    """

    # ===== setup =====
    _progress(1, "init")
    ffmpeg_path = _which_ffmpeg()

    storage_path = _ensure_dir(storage_dir)
    out_dir = _ensure_dir(storage_path / job_id)

    # output template: yt-dlp replace %(ext)s
    outtmpl = str(out_dir / "%(title).80s.%(ext)s")

    # ===== yt-dlp command =====
    _progress(5, "downloading")

    if file_type == "mp4":
        height = None
        if quality and quality.endswith("p"):
            try:
                height = int(quality.replace("p", ""))
            except:
                height = None

        if height:
            fmt = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best"
        else:
            fmt = "bestvideo+bestaudio/best"

        cmd = [
            "yt-dlp",
            url,
            "-f", fmt,
            "--merge-output-format", "mp4",
            "-o", outtmpl,
            "--ffmpeg-location", ffmpeg_path,
            "--no-playlist",
        ]

    else:  # mp3
        if bitrate is None:
            bitrate = 192

        cmd = [
            "yt-dlp",
            url,
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", str(bitrate),
            "-o", outtmpl,
            "--ffmpeg-location", ffmpeg_path,
            "--no-playlist",
        ]

    # ===== run =====
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )

    # parsing progress dari output yt-dlp
    for line in proc.stdout:
        line = line.strip()

        # contoh: [download]  12.3% of ...
        if "[download]" in line and "%" in line:
            try:
                left = line.split("%")[0]
                pct_str = left.split()[-1]
                pct = float(pct_str)

                # map download pct (0-100) -> progress 5-85
                mapped = 5 + int((pct / 100) * 80)
                _progress(mapped, "downloading")
            except:
                pass

        if "Destination:" in line:
            _progress(86, "postprocess")

        if "Merging formats" in line or "ExtractAudio" in line:
            _progress(90, "postprocess")

    ret = proc.wait()
    if ret != 0:
        _progress(100, "failed")
        raise RuntimeError("yt-dlp gagal. Pastikan URL valid, yt-dlp & ffmpeg tersedia.")

    _progress(95, "finalizing")

    # ===== cari file output =====
    files = list(out_dir.glob("*"))
    if not files:
        _progress(100, "failed")
        raise RuntimeError("Output file tidak ditemukan setelah download selesai.")

    files.sort(key=lambda p: p.stat().st_size, reverse=True)
    output_file = files[0]

    _progress(100, "done")

    return {
        "job_id": job_id,
        "type": file_type,
        "file_name": output_file.name,
        "file_path": str(output_file),
        "download_url": f"/api/youtube/download/{job_id}",
        "status": "finished",
    }
