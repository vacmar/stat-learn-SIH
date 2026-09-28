import os

import fakeredis
import pytest

# Tests must not block on a live Exasol instance.
os.environ.setdefault("EXASOL_ENABLED", "false")
os.environ.setdefault("EXASOL_PASSWORD", "")

# Isolate path/lesson Redis caches from the developer's docker Redis.
_fake_redis = fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture(scope="session", autouse=True)
def disable_exasol_for_tests():
    os.environ["EXASOL_ENABLED"] = "false"
    os.environ["EXASOL_PASSWORD"] = ""


@pytest.fixture(autouse=True)
def isolate_redis(monkeypatch):
    """All direct get_redis_client() calls use fakeredis, not localhost:6379."""
    _fake_redis.flushall()
    monkeypatch.setattr(
        "app.core.cache.get_redis_client", lambda: _fake_redis, raising=False
    )
    # Reset module singleton if already created
    import app.core.cache as cache_mod

    monkeypatch.setattr(cache_mod, "redis_client", _fake_redis, raising=False)
    yield
    _fake_redis.flushall()
