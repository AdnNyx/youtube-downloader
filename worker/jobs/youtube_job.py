import os
import subprocess
from yt_dlp import YoutubeDL


def run_ffmpeg_convert_to_mp3(input_path: str, output_path: str, bitrate: int = 192):
    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-b:a", f"{bitrate}k",
        output_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def download_job(url: str, job_id: str, job_type: str, quality: str = None, bitrate: int = 192, storage_dir: str = "backend/storage"):
    """
    Worker job:
    - download mp4/mp3
    - save output in storage_dir/job_id/
    """
    job_dir = os.path.join(storage_dir, job_id)
    os.makedirs(job_dir, exist_ok=True)

    # output templates
    outtmpl = os.path.join(job_dir, "%(title)s.%(ext)s")

    if job_type == "mp4":
        # pilih format mp4
        # quality contoh: "720p"
        # strategy: ambil bestvideo+audio untuk resolusi target, fallback best
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
            "merge_output_format": "mp4"
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "video")
            filename = f"{title}.mp4"
            return {"filename": filename, "path": os.path.join(job_dir, filename)}

    elif job_type == "mp3":
        # download audio best dulu (m4a/webm), lalu convert mp3
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": outtmpl,
            "noplaylist": True,
            "quiet": True
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "audio")

        # cari file audio yang terdownload
        # yt-dlp akan simpan sesuai ext sumber
        downloaded = None
        for f in os.listdir(job_dir):
            if f.lower().startswith(title.lower()):
                if f.endswith(".webm") or f.endswith(".m4a") or f.endswith(".mp4"):
                    downloaded = os.path.join(job_dir, f)
                    break

        if not downloaded:
            raise RuntimeError("Downloaded audio file not found")

        output_mp3 = os.path.join(job_dir, f"{title}.mp3")
        run_ffmpeg_convert_to_mp3(downloaded, output_mp3, bitrate=bitrate)

        return {"filename": f"{title}.mp3", "path": output_mp3}

    else:
        raise ValueError("Invalid job_type")
