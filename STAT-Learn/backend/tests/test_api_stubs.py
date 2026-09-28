from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.core.cache import get_redis_client
from app.main import app
from app.models.domain import LearningPath, NodeStatus, PathNode
from app.repository import state_repo
from tests.test_caching import fake_redis

app.dependency_overrides[get_redis_client] = lambda: fake_redis
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    fake_redis.flushall()
    state_repo.db["paths"].clear()
    state_repo.db["nodes"].clear()
    state_repo.db["learning_progress"].clear()
    state_repo.db["learner_profiles"]["L1"] = {"target_role": "role_be"}


def test_path_generate_python_first(monkeypatch):
    from app.models.domain import Learner
    from app.services import ai_client, replanning_service

    learner = Learner(
        learner_id="L1",
        account_id="a1",
        name="Demo",
        target_role_id="role_be",
        created_at=datetime.now(UTC).isoformat(),
        updated_at=datetime.now(UTC).isoformat(),
    )
    state_repo.create_learner(learner)

    res = client.post("/paths/generate")
    assert res.status_code == 401  # requires auth cookie

    def fake_ai(_payload):
        return {
            "summary": "Backend path",
            "target_role": "Backend Developer",
            "stages": [
                {
                    "stage_number": 1,
                    "course_name": "Python Basics",
                    "rationale": "Language foundation",
                    "target_skills": ["Python"],
                },
                {
                    "stage_number": 2,
                    "course_name": "SQL Basics",
                    "rationale": "Data access",
                    "target_skills": ["SQL"],
                },
            ],
            "gap_analysis_summary": "Gaps closed",
            "estimated_total_hours": 40,
            "capstone": {
                "title": "Build a Simple API",
                "description": "Create a FastAPI application with two endpoints.",
                "requirements": [
                    {
                        "requirement_id": "req_fastapi",
                        "description": "Must use FastAPI",
                        "mandatory": True,
                    }
                ],
            },
        }

    monkeypatch.setattr(ai_client, "request_ai_pathway", fake_ai)
    out = replanning_service.generate_path_for_learner("L1", "role_be")
    course_ids = [n["course_id"] for n in out["nodes"]]
    assert course_ids[0].startswith("ai_")
    assert out["nodes"][0]["status"] == "UNLOCKED"
    assert out["nodes"][1]["status"] == "LOCKED"
    titles = [state_repo.db["courses"][n["course_id"]]["title"] for n in out["nodes"]]
    assert titles[0] == "Python Basics"
    assert state_repo.db["learner_profiles"]["L1"]["recommended_project_id"]


def test_ai_android_path_not_fastapi(monkeypatch):
    from app.models.domain import Learner
    from app.services import ai_client, replanning_service

    learner = Learner(
        learner_id="L_android",
        account_id="a2",
        name="Android Learner",
        target_role_id="role_other",
        target_domain="React Native",
        known_skills=["React.js"],
        goals=["Become a Android Developer"],
        created_at=datetime.now(UTC).isoformat(),
        updated_at=datetime.now(UTC).isoformat(),
    )
    state_repo.create_learner(learner)
    state_repo.db["learner_profiles"]["L_android"] = {
        "target_role": "role_other",
        "role_title": "Android Developer",
    }

    def fake_ai(payload):
        assert "Android" in payload["target_role"]
        return {
            "summary": "Mobile path",
            "target_role": "Android Developer",
            "stages": [
                {
                    "stage_number": 1,
                    "course_name": "JavaScript Fundamentals",
                    "rationale": "Foundation",
                    "target_skills": ["JavaScript"],
                },
                {
                    "stage_number": 2,
                    "course_name": "React Native Basics",
                    "rationale": "Mobile",
                    "target_skills": ["React Native"],
                },
                {
                    "stage_number": 3,
                    "course_name": "Android App Foundations",
                    "rationale": "Platform",
                    "target_skills": ["Android"],
                },
            ],
            "gap_analysis_summary": "Mobile gaps",
            "estimated_total_hours": 50,
            "capstone": {
                "title": "Build a Mobile Screen Flow",
                "description": "Create a React Native app with navigation.",
                "requirements": [
                    {
                        "requirement_id": "req_rn",
                        "description": "Must use React Native",
                        "mandatory": True,
                    }
                ],
            },
        }

    monkeypatch.setattr(ai_client, "request_ai_pathway", fake_ai)
    out = replanning_service.generate_path_for_learner("L_android", "role_other")
    titles = [state_repo.db["courses"][n["course_id"]]["title"] for n in out["nodes"]]
    assert "JavaScript Fundamentals" in titles
    assert not any("Python" in t for t in titles)
    proj_id = state_repo.db["learner_profiles"]["L_android"]["recommended_project_id"]
    proj = state_repo.db["projects"][proj_id]
    assert "FastAPI" not in proj["description"]
    assert "React Native" in proj["description"]


def test_node_start_and_progress():
    path_id = "p_stub"
    state_repo.save_path(
        LearningPath(
            path_id=path_id,
            learner_id="L1",
            version=1,
            created_at=datetime.now(UTC).isoformat(),
            is_active=True,
        )
    )
    node = PathNode(
        node_id="n_stub",
        path_id=path_id,
        course_id="c_py",
        sequence_order=1,
        status=NodeStatus.UNLOCKED,
    )
    state_repo.update_node(node)

    res = client.post(
        "/nodes/n_stub/start",
        json={"learner_id": "L1", "current_module": "lesson"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "IN_PROGRESS"
    assert data["progress"]["started_at"]

    prog = client.get("/nodes/n_stub/progress?learner_id=L1")
    assert prog.status_code == 200
    assert prog.json()["progress"]["current_module"] == "lesson"


def test_assessment_scoring_not_flat_85():
    client.post("/assessments/start?assessment_id=a_stub")
    client.post(
        "/assessments/a_stub/answer",
        json={"question_id": "py_q1", "answer": "def"},
    )
    client.post(
        "/assessments/a_stub/answer",
        json={"question_id": "py_q2", "answer": "wrong"},
    )
    fin = client.post("/assessments/a_stub/finalize")
    assert fin.status_code == 200
    score = fin.json()["result"]["score"]
    assert score != 85.0
    assert score == 50.0
