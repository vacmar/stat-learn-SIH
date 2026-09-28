import redis

from app.core.config import settings

redis_client = None


def get_redis_client() -> redis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=0.4,
            socket_timeout=0.4,
        )
    return redis_client


def save_session(session_id: str, account_id: str, expiry: int) -> None:
    get_redis_client().setex(f"session:{session_id}", expiry, account_id)


def load_session(session_id: str) -> str | None:
    value = get_redis_client().get(f"session:{session_id}")
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)


def drop_session(session_id: str) -> None:
    get_redis_client().delete(f"session:{session_id}")
