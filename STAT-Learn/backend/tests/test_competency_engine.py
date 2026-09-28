"""Deterministic competency scoring and attempt API."""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.core.cache import get_redis_client
from app.data.diagnostic_seed import (
    DEMO_LEARNER_HEADER,
    DEMO_LEARNER_TOKEN,
    QUESTIONS,
    SCREENING_ANSWER_INDEX,
)
from app.main import app
from app.models.domain import Learner
from app.repository import state_repo
from app.services.competency_engine import (
    demonstrated_level,
    display_percent,
    gap_and_status,
    level_met,
    score_competency,
)
from app.services.competency_store import reset_memory

client = TestClient(app)
HEADER = {DEMO_LEARNER_HEADER: DEMO_LEARNER_TOKEN}


@pytest.fixture(autouse=True)
def clean_attempts():
    reset_memory()
    yield
    reset_memory()


def test_threshold_boundaries():
    assert level_met(59, 100) is False
    assert level_met(60, 100) is True
    assert level_met(61, 100) is True
    assert level_met(0, 0) is False
    assert display_percent(3, 5) == 60


def test_demonstrated_level_requires_lower_levels():
    assert demonstrated_level({1: (1, 1), 2: (60, 100)}) == 2
    assert demonstrated_level({1: (1, 1), 2: (59, 100)}) == 1
    assert demonstrated_level({1: (0, 1), 2: (100, 100)}) is None
    assert demonstrated_level({2: (1, 1)}) is None


def test_gap_status_bands():
    assert gap_and_status(4, 4) == (0, "Meets Target", "Low")
    assert gap_and_status(4, 3) == (1, "Moderate Gap", "Medium")
    assert gap_and_status(4, 2) == (2, "Priority Gap", "High")
    assert gap_and_status(3, None) == (3, "Priority Gap", "High")


def test_grouping_percentage_and_evidence():
    questions = [
        {"id": "a", "level": 1, "topic": "reading a table", "correct_answer": "yes"},
        {"id": "b", "level": 1, "topic": "reading a table", "correct_answer": "yes"},
        {"id": "c", "level": 2, "topic": "comparing figures", "correct_answer": "yes"},
        {"id": "d", "level": 3, "topic": "statistical interpretation", "correct_answer": "yes"},
        {"id": "e", "level": 3, "topic": "statistical interpretation", "correct_answer": "yes"},
    ]
    answers = {"a": "yes", "b": "yes", "c": "yes", "d": "no", "e": "no"}
    result = score_competency(
        competency_id="stat-data-analysis",
        name="Statistical Data Analysis",
        domain="STAT",
        target_level=4,
        questions=questions,
        answers_by_question=answers,
    )
    assert result["score_percent"] == 60
    assert result["current_level"] == "L2"
    assert result["target_level"] == "L4"
    assert result["gap"] == 2
    assert result["status"] == "Priority Gap"
    assert result["priority"] == "High"
    assert result["evidence"]["correct"] == 3
    assert result["evidence"]["evaluated"] == 5
    assert result["evidence"]["incorrect_question_ids"] == ["d", "e"]
    assert result["evidence"]["incorrect_topics"] == ["statistical interpretation"]


def _screening_body(question_id: str) -> dict:
    question = next(item for item in QUESTIONS if item.id == question_id)
    index = SCREENING_ANSWER_INDEX.get(question_id, 0)
    return {"question_id": question_id, "selected_answer": question.options[index]}


def _complete_screening() -> dict:
    created = client.post("/assessments/attempts", headers=HEADER)
    assert created.status_code == 200
    attempt_id = created.json()["attempt_id"]
    for question in QUESTIONS:
        posted = client.post(
            f"/assessments/attempts/{attempt_id}/answers",
            headers=HEADER,
            json=_screening_body(question.id),
        )
        assert posted.status_code == 200, posted.text
    completed = client.post(f"/assessments/attempts/{attempt_id}/complete", headers=HEADER)
    assert completed.status_code == 200, completed.text
    return completed.json()


def test_screening_pattern_produces_expected_gaps():
    result = _complete_screening()
    by_id = {row["competency_id"]: row for row in result["competencies"]}
    analysis = by_id["stat-data-analysis"]
    survey = by_id["stat-survey-methodology"]
    quality = by_id["stat-data-quality"]
    assert analysis["current_level"] == "L2"
    assert analysis["gap"] == 2
    assert analysis["status"] == "Priority Gap"
    assert survey["current_level"] == "L2"
    assert survey["gap"] == 1
    assert survey["status"] == "Moderate Gap"
    assert quality["current_level"] == "L3"
    assert quality["gap"] == 1
    assert quality["status"] == "Moderate Gap"
    assert result["priority_gap_count"] == 1


def test_diagnostic_hides_answer_key():
    res = client.get("/assessments/diagnostic", headers=HEADER)
    assert res.status_code == 200
    payload = res.json()
    assert payload["question_count"] == len(QUESTIONS)
    assert "correct" not in payload["questions"][0]
    assert "correct_index" not in payload["questions"][0]


def test_rejects_missing_identity_and_foreign_token():
    assert client.get("/assessments/diagnostic").status_code == 401
    assert client.get("/assessments/diagnostic", headers={DEMO_LEARNER_HEADER: "someone-else"}).status_code == 401


def test_duplicate_invalid_and_completed_attempt():
    created = client.post("/assessments/attempts", headers=HEADER)
    attempt_id = created.json()["attempt_id"]
    first = QUESTIONS[0]
    ok = client.post(
        f"/assessments/attempts/{attempt_id}/answers",
        headers=HEADER,
        json={"question_id": first.id, "selected_answer": first.options[0]},
    )
    assert ok.status_code == 200
    duplicate = client.post(
        f"/assessments/attempts/{attempt_id}/answers",
        headers=HEADER,
        json={"question_id": first.id, "selected_answer": first.options[1]},
    )
    assert duplicate.status_code == 409
    invalid = client.post(
        f"/assessments/attempts/{attempt_id}/answers",
        headers=HEADER,
        json={"question_id": QUESTIONS[1].id, "selected_answer": "not an option"},
    )
    assert invalid.status_code == 422
    unknown = client.post(
        f"/assessments/attempts/{attempt_id}/answers",
        headers=HEADER,
        json={"question_id": "missing", "selected_answer": "x"},
    )
    assert unknown.status_code == 422
    scored = client.post(
        f"/assessments/attempts/{attempt_id}/answers",
        headers=HEADER,
        json={"question_id": QUESTIONS[1].id, "selected_answer": QUESTIONS[1].options[0], "score": 100},
    )
    assert scored.status_code == 422
    incomplete = client.post(f"/assessments/attempts/{attempt_id}/complete", headers=HEADER)
    assert incomplete.status_code == 422


def test_other_learner_cannot_modify_attempt():
    created = client.post("/assessments/attempts", headers=HEADER)
    attempt_id = created.json()["attempt_id"]
    now = datetime.now(UTC).isoformat()
    other = Learner(
        learner_id="learner_other",
        account_id="account_other",
        name="Other Official",
        created_at=now,
        updated_at=now,
    )
    state_repo.create_learner(other)
    get_redis_client().set("session:other", other.account_id)
    client.cookies.set("session_id", "other")
    res = client.post(
        f"/assessments/attempts/{attempt_id}/answers",
        json={"question_id": QUESTIONS[0].id, "selected_answer": QUESTIONS[0].options[0]},
    )
    assert res.status_code == 403
    client.cookies.clear()


def test_completed_attempt_is_frozen_and_result_matches_profile():
    result = _complete_screening()
    attempt_id = result["attempt_id"]
    frozen = client.post(
        f"/assessments/attempts/{attempt_id}/answers",
        headers=HEADER,
        json={"question_id": QUESTIONS[0].id, "selected_answer": QUESTIONS[0].options[0]},
    )
    assert frozen.status_code == 409
    again = client.post(f"/assessments/attempts/{attempt_id}/complete", headers=HEADER)
    assert again.status_code == 409
    loaded = client.get(f"/assessments/attempts/{attempt_id}/result", headers=HEADER)
    assert loaded.status_code == 200
    assert loaded.json()["overall_score_percent"] == result["overall_score_percent"]
    profile = client.get("/competencies/profile", headers=HEADER)
    assert profile.status_code == 200
    body = profile.json()
    assert body["assessed"] is True
    assert body["overall_score_percent"] == result["overall_score_percent"]
    assert body["attempt_id"] == attempt_id
    gap = client.get("/competencies/gaps/stat-data-analysis", headers=HEADER)
    assert gap.status_code == 200
    assert gap.json()["evidence"]["incorrect_question_ids"] == ["sda-l3-a", "sda-l3-b"]
    history = client.get("/competencies/history", headers=HEADER)
    assert history.status_code == 200
    assert history.json()["attempts"][0]["attempt_id"] == attempt_id
    assert history.json()["attempts"][0]["status"] == "completed"


def test_open_attempt_has_no_result():
    created = client.post("/assessments/attempts", headers=HEADER)
    attempt_id = created.json()["attempt_id"]
    res = client.get(f"/assessments/attempts/{attempt_id}/result", headers=HEADER)
    assert res.status_code == 409
