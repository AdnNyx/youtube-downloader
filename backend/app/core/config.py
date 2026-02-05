import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "YouTube Downloader API")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    ENV: str = os.getenv("ENV", "development")

    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

    STORAGE_DIR: str = os.getenv("STORAGE_DIR", "storage")
    JOB_TTL_SECONDS: int = int(os.getenv("JOB_TTL_SECONDS", "3600"))

settings = Settings()
