from typing import Optional
from pydantic import BaseModel

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
}

class Settings(BaseModel):
    request_timeout_seconds: float = 15.0
    max_redirects: int = 5
    verify_ssl: bool = True
    user_agent: str = DEFAULT_HEADERS["User-Agent"]
    sqlite_url: str = "sqlite:///brand_insights.db"

settings = Settings()
