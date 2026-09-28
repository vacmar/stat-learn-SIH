from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core.cache import get_redis_client
from app.main import app
from app.repository import state_repo
from tests.test_caching import fake_redis

# We don't redefine fake_redis or dependency_overrides here to avoid pollution
# It is already overridden in test_caching.py which pytest loads.
# However, to be safe, we ensure it uses the same instance.
app.dependency_overrides[get_redis_client] = lambda: fake_redis

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    fake_redis.flushall()
    state_repo.db["conversations"] = {}
    state_repo.db["summaries"] = {}
    state_repo.db["mistakes"] = {}
    state_repo.db["lessons"] = {
        "n1": {
            "lesson": "Mock lesson",
            "concepts": ["Concept 1"],
            "exercises": [],
            "hints": [],
        }
    }


def test_node_context_retrieval():
    res = client.get("/nodes/n1/context")
    assert res.status_code == 200
    assert res.json()["lesson"] == "Mock lesson"


def test_mistake_creation_and_retrieval():
    payload = {"learner_id": "L1", "concept": "loops", "description": "infinite loop"}
    res = client.post("/nodes/n1/mistakes", json=payload)
    assert res.status_code == 200

    # Retrieve weak concepts
    res2 = client.get("/nodes/n1/mistakes?learner_id=L1")
    assert res2.status_code == 200
    concepts = res2.json()["weak_concepts"]
    assert len(concepts) == 1
    assert concepts[0]["concept"] == "loops"
    assert concepts[0]["error_count"] == 1


def test_learner_node_isolation():
    client.post(
        "/nodes/n1/mistakes",
        json={"learner_id": "L1", "concept": "A", "description": "desc"},
    )
    client.post(
        "/nodes/n1/mistakes",
        json={"learner_id": "L2", "concept": "B", "description": "desc"},
    )

    res = client.get("/nodes/n1/mistakes?learner_id=L1")
    concepts = res.json()["weak_concepts"]
    assert len(concepts) == 1
    assert concepts[0]["concept"] == "A"


def test_weak_concept_aggregation():
    client.post(
        "/nodes/n1/mistakes",
        json={"learner_id": "L1", "concept": "A", "description": "first error"},
    )
    client.post(
        "/nodes/n1/mistakes",
        json={"learner_id": "L1", "concept": "A", "description": "second error"},
    )

    res = client.get("/nodes/n1/mistakes?learner_id=L1")
    concepts = res.json()["weak_concepts"]
    assert len(concepts) == 1
    assert concepts[0]["error_count"] == 2
    assert concepts[0]["latest_description"] == "second error"


def test_conversation_summary_update():
    # Send 5 messages to trigger rolling summary
    for i in range(5):
        client.post(
            "/conversations/conv_summary/messages",
            json={"role": "user", "content": f"msg {i}"},
        )

    res = client.get("/conversations/conv_summary")
    summary = res.json()["summary"]
    # The background task should have updated it
    assert "Summarized 5 messages" in summary


def test_summary_does_not_replace_durable_history():
    for i in range(5):
        client.post(
            "/conversations/conv_durable/messages",
            json={"role": "user", "content": f"msg {i}"},
        )

    # Check DB directly
    db_history = state_repo.get_conversation("conv_durable")
    assert len(db_history) == 5

    # Check API limit returns only last 3, but summary is still active
    res = client.get("/conversations/conv_durable?limit=3")
    assert len(res.json()["recent_messages"]) == 3
    assert "Summarized 5 messages" in res.json()["summary"]


@patch("app.api.conversations.redis.Redis.lrange", side_effect=Exception("Redis down"))
def test_redis_failure_does_not_destroy_history(mock_lrange):
    # Post directly to DB
    state_repo.save_conversation_message(
        "conv_fail", {"role": "user", "content": "hello"}
    )

    res = client.get("/conversations/conv_fail")
    assert res.status_code == 200
    assert len(res.json()["recent_messages"]) == 1
