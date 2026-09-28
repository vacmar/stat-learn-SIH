"""Course study stays on the server and uses the 0.60 completion rule."""

from fastapi.testclient import TestClient

from app.data.catalogue_seed import PROGRAMMES
from app.data.course_questions import COURSE_QUESTIONS
from app.data.diagnostic_seed import DEMO_LEARNER_HEADER, DEMO_LEARNER_ID, DEMO_LEARNER_TOKEN
from app.main import app
from app.repository import sqlite_db

client = TestClient(app)
HEADER = {DEMO_LEARNER_HEADER: DEMO_LEARNER_TOKEN}


def _answers(programme_id: str, correct: bool) -> list[dict]:
    rows = []
    for question in COURSE_QUESTIONS[programme_id]:
        index = question.correct_index if correct else (question.correct_index + 1) % 4
        rows.append({"question_id": question.id, "selected_answer": question.options[index]})
    return rows


def test_every_catalogue_course_has_questions():
    assert set(COURSE_QUESTIONS) == {item.id for item in PROGRAMMES}
    for questions in COURSE_QUESTIONS.values():
        assert len(questions) == 3


def test_course_hides_the_answer_key_and_records_completion():
    programme_id = "igot-official-analysis"
    shown = client.get(f"/competencies/catalogue/{programme_id}", headers=HEADER)
    assert shown.status_code == 200
    body = shown.json()
    assert "correct_index" not in shown.text
    assert len(body["questions"]) == 3
    assert body["questions"][0]["options"]

    failed = client.post(
        f"/competencies/catalogue/{programme_id}/submit",
        headers=HEADER,
        json={"answers": _answers(programme_id, correct=False)},
    )
    assert failed.status_code == 200
    assert failed.json()["passed_this_attempt"] is False
    assert failed.json()["status"] == "Not yet"

    passed = client.post(
        f"/competencies/catalogue/{programme_id}/submit",
        headers=HEADER,
        json={"answers": _answers(programme_id, correct=True)},
    )
    assert passed.status_code == 200
    assert passed.json()["passed_this_attempt"] is True
    assert passed.json()["status"] == "Completed"
    assert "correct_option" not in passed.text

    again = client.get(f"/competencies/catalogue/{programme_id}", headers=HEADER)
    assert again.json()["progress"]["passed"] is True
    with sqlite_db.connect() as conn:
        conn.execute(
            "DELETE FROM course_progress WHERE learner_id = ? AND programme_id = ?",
            (DEMO_LEARNER_ID, programme_id),
        )
