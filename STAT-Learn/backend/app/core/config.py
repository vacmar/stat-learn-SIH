import os
from urllib.parse import urlparse


def _redis_settings_from_env() -> tuple[str, int, int]:
    url = os.getenv("REDIS_URL", "").strip()
    if url:
        parsed = urlparse(url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 6379
        db = 0
        if parsed.path and parsed.path.strip("/"):
            try:
                db = int(parsed.path.strip("/"))
            except ValueError:
                db = 0
        return host, port, db
    return (
        os.getenv("REDIS_HOST", "localhost"),
        int(os.getenv("REDIS_PORT", "6379")),
        int(os.getenv("REDIS_DB", "0")),
    )


class Settings:
    def __init__(self) -> None:
        host, port, db = _redis_settings_from_env()
        self.REDIS_HOST = host
        self.REDIS_PORT = port
        self.REDIS_DB = db


settings = Settings()
