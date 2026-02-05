import os
import re
import subprocess
from yt_dlp import YoutubeDL
from app.redis_meta import set_meta


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[\\/:*?"<>|]', "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:120] if len(name) > 120 else name


def run_ffmpeg_convert_to_mp3(input_path: str, output_path: str, bitrate: int = 192):
    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-vn",
        "-b:a", f"{bitrate}k",
        output_path
    ]
    subprocess.run(cmd, check=True)


def download_job(url: str, job_id: str, job_type: str, quality: str = None, bitrate: int = 192, storage_dir: str = "storage"):
    """
    Worker job with progress tracking:
    - update Redis meta
    """
    def update(status: str, stage: str, progress: int, **extra):
        payload = {
            "status": status,
            "stage": stage,
            "progress": max(0, min(int(progress), 100)),
            "filename": extra.get("filename"),
            "path": extra.get("path"),
            "error": extra.get("error"),
        }
        set_meta(job_id, payload)

    job_dir = os.path.join(storage_dir, job_id)
    os.makedirs(job_dir, exist_ok=True)

    update("processing", "starting", 1)

    # progress hook yt-dlp
    def hook(d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes")
            if total and downloaded:
                pct = int(downloaded * 70 / total)  # 0-70% untuk download
                update("processing", "downloading", pct)
        elif d["status"] == "finished":
            update("processing", "downloaded", 75)

    outtmpl = os.path.join(job_dir, "%(title)s.%(ext)s")

    try:
        if job_type == "mp4":
            height = None
            if quality and quality.endswith("p"):
                try:
                    height = int(quality.replace("p", ""))
                except:
                    height = None

            if height:
                fmt = f"bestvideo[ext=mp4][height<={height}]+bestaudio[ext=m4a]/best[ext=mp4]/best"
            else:
                fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"

            ydl_opts = {
                "format": fmt,
                "outtmpl": outtmpl,
                "noplaylist": True,
                "quiet": True,
                "merge_output_format": "mp4",
                "progress_hooks": [hook],
            }

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

            title = sanitize_filename(info.get("title", "video"))
            filename = f"{title}.mp4"
            path = os.path.join(job_dir, filename)

            update("processing", "finalizing", 95, filename=filename, path=path)
            update("finished", "done", 100, filename=filename, path=path)
            return {"filename": filename, "path": path}

        elif job_type == "mp3":
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": outtmpl,
                "noplaylist": True,
                "quiet": True,
                "progress_hooks": [hook],
            }

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

            title = sanitize_filename(info.get("title", "audio"))

            # cari file audio terdownload
            update("processing", "locating_audio", 78)
            downloaded = None
            for f in os.listdir(job_dir):
                lower = f.lower()
                if lower.endswith(".webm") or lower.endswith(".m4a") or lower.endswith(".mp4"):
                    downloaded = os.path.join(job_dir, f)
                    break

            if not downloaded:
                raise RuntimeError("Downloaded audio file not found")

            output_mp3 = os.path.join(job_dir, f"{title}.mp3")

            update("processing", "converting", 85, filename=f"{title}.mp3")
            run_ffmpeg_convert_to_mp3(downloaded, output_mp3, bitrate=bitrate)

            update("finished", "done", 100, filename=f"{title}.mp3", path=output_mp3)
            return {"filename": f"{title}.mp3", "path": output_mp3}

        else:
            raise ValueError("Invalid job_type")

    except Exception as e:
        update("failed", "error", 0, error=str(e))
        raise
