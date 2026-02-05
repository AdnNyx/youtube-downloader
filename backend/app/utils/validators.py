from urllib.parse import urlparse

ALLOWED_DOMAINS = {"www.youtube.com", "youtube.com", "m.youtube.com", "youtu.be"}

def is_allowed_youtube_url(url: str) -> bool:
    try:
        domain = urlparse(url).netloc.lower()
        return domain in ALLOWED_DOMAINS
    except Exception:
        return False
