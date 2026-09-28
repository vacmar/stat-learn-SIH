from unittest.mock import patch

import fakeredis
import pytest
from fastapi.testclient import TestClient

from app.core.cache import get_redis_client
from app.main import app
from app.models.domain import NodeStatus, PathNode
from app.repository import state_repo

fake_redis = fakeredis.FakeRedis(decode_responses=True)
app.dependency_overrides[get_redis_client] = lambda: fake_redis

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    fake_redis.flushall()
    state_repo.db["conversations"] = {}
    state_repo.db["assessments"] = {}
    state_repo.db["nodes"] = {}


def test_1_db_first_conversation_durability():
    client.post(
        "/conversations/conv_1/messages", json={"role": "user", "content": "hello"}
    )
    # DB contains message
    assert len(state_repo.db["conversations"]["conv_1"]) == 1
    # Redis contains message
    assert fake_redis.exists("conversations:conv_1:messages")


def test_2_cache_miss():
    # Insert directly to DB (bypass Redis)
    state_repo.db["conversations"]["conv_2"] = [
        {"role": "user", "content": "miss_test"}
    ]
    assert not fake_redis.exists("conversations:conv_2:messages")

    # Read should hit DB, populate Redis, and return
    res = client.get("/conversations/conv_2")
    assert res.status_code == 200
    assert len(res.json()["recent_messages"]) == 1
    assert fake_redis.exists("conversations:conv_2:messages")


@patch("app.api.conversations.redis.Redis.lrange", side_effect=Exception("Redis down"))
def test_3_redis_failure_fallback(mock_lrange):
    # Insert directly to DB
    state_repo.db["conversations"]["conv_3"] = [
        {"role": "user", "content": "fallback_test"}
    ]

    # Read should fallback to DB despite Redis failure
    res = client.get("/conversations/conv_3")
    assert res.status_code == 200
    assert len(res.json()["recent_messages"]) == 1


def test_4_assessment_finalization():
    client.post("/assessments/start?assessment_id=a1")
    client.post("/assessments/a1/answer", json={"question_id": "q1", "answer": "ans"})

    # Finalize
    res = client.post("/assessments/a1/finalize")
    assert res.status_code == 200

    # DB contains final result
    assert "a1" in state_repo.db["assessments"]

    # Redis key deleted
    assert not fake_redis.exists("assessments:active:a1")


@patch(
    "app.repository.state_repo.save_assessment_result", side_effect=Exception("DB down")
)
def test_5_finalization_failure_safety(mock_save):
    client.post("/assessments/start?assessment_id=a2")
    client.post("/assessments/a2/answer", json={"question_id": "q1", "answer": "ans"})

    # Finalize fails
    res = client.post("/assessments/a2/finalize")
    assert res.status_code == 500

    # Redis state is NOT deleted
    assert fake_redis.exists("assessments:active:a2")


@patch("app.services.cache_service.get_redis_client")
def test_6_node_completion_ordering(mock_get_redis):
    mock_get_redis.return_value = fake_redis

    state_repo.db["nodes"]["n1"] = PathNode(
        node_id="n1",
        path_id="p1",
        course_id="c1",
        sequence_order=1,
        status=NodeStatus.IN_PROGRESS,
    )
    fake_redis.set("conversations:conv_n1:messages", "data")

    from app.models.payloads import CompletionRequest
    from app.services.progression_service import attempt_completion

    # Trigger completion
    attempt_completion(
        "L1",
        "n1",
        CompletionRequest(learner_id="L1", assessment_score=85.0, practical_pass=True),
    )

    # Validate DB is completed
    assert state_repo.db["nodes"]["n1"].status == NodeStatus.COMPLETED
    # Validate cache is invalidated
    assert not fake_redis.exists("conversations:conv_n1:messages")


def test_7_ttl_rules():
    client.post(
        "/conversations/conv_4/messages", json={"role": "user", "content": "ttl"}
    )
    assert fake_redis.ttl("conversations:conv_4:messages") > 0

    client.post("/assessments/start?assessment_id=a3")
    assert fake_redis.ttl("assessments:active:a3") > 0


def test_8_learner_isolation():
    client.post(
        "/conversations/L1/messages", json={"role": "user", "content": "I am L1"}
    )
    client.post(
        "/conversations/L2/messages", json={"role": "user", "content": "I am L2"}
    )

    res1 = client.get("/conversations/L1")
    res2 = client.get("/conversations/L2")

    assert res1.json()["recent_messages"][0]["content"] == "I am L1"
    assert res2.json()["recent_messages"][0]["content"] == "I am L2"
