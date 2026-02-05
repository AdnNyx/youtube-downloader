from yt_dlp import YoutubeDL
from typing import Dict, List, Any


YDL_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "noplaylist": True,
}


def parse_youtube(url: str) -> Dict[str, Any]:
    """
    Return:
      - id, title, channel, duration, thumbnail
      - formats: mp4 list + audio list
    """
    with YoutubeDL(YDL_OPTS) as ydl:
        info = ydl.extract_info(url, download=False)

    # basic metadata
    video_id = info.get("id")
    title = info.get("title")
    channel = info.get("uploader") or info.get("channel")
    duration = info.get("duration")
    thumbnail = info.get("thumbnail")

    formats = info.get("formats", [])

    mp4_formats: List[Dict[str, Any]] = []
    audio_formats: List[Dict[str, Any]] = []

    for f in formats:
        ext = f.get("ext")
        vcodec = f.get("vcodec")
        acodec = f.get("acodec")
        itag = f.get("format_id")
        height = f.get("height")
        abr = f.get("abr")  # audio bitrate
        filesize = f.get("filesize") or f.get("filesize_approx")

        # audio-only
        if vcodec == "none" and acodec != "none":
            label = f"{ext} {int(abr)}kbps" if abr else f"{ext} audio"
            audio_formats.append({
                "label": label,
                "itag": int(itag) if str(itag).isdigit() else None,
                "ext": ext,
                "hasAudio": True,
                "vcodec": vcodec,
                "acodec": acodec,
                "filesize": filesize,
            })

        # video (mp4 only for now)
        if ext == "mp4" and vcodec != "none":
            label = f"{height}p" if height else "mp4"
            mp4_formats.append({
                "label": label,
                "itag": int(itag) if str(itag).isdigit() else None,
                "ext": ext,
                "hasAudio": acodec != "none",
                "vcodec": vcodec,
                "acodec": acodec,
                "filesize": filesize,
            })

    # sorting
    def mp4_sort_key(x):
        # sort by height extracted from label
        try:
            return int(x["label"].replace("p", ""))
        except Exception:
            return 0

    mp4_formats = sorted(mp4_formats, key=mp4_sort_key)
    audio_formats = sorted(audio_formats, key=lambda x: x.get("filesize") or 0)

    return {
        "id": video_id,
        "title": title,
        "channel": channel,
        "duration": duration,
        "thumbnail": thumbnail,
        "formats": {
            "mp4": mp4_formats,
            "audio": audio_formats,
        },
        # untuk debugging (opsional)
        # "raw": info,
    }
