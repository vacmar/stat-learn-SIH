"""Study and completion for catalogue courses. Scoring uses the same 0.60 ratio and does not call a model."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException

from app.data.catalogue_seed import PROGRAMME_BY_ID, public_programme
from app.data.course_questions import COURSE_QUESTIONS
from app.repository import sqlite_db
from app.services.competency_engine import display_percent, level_met
from app.services.igot_catalogue import public_course, questions_for


def _questions(programme_id: str):
    programme = PROGRAMME_BY_ID.get(programme_id)
    questions = COURSE_QUESTIONS.get(programme_id)
    if programme is None or not questions:
        raise HTTPException(status_code=404, detail="Course not found")
    return programme, questions


def course_for_learner(programme_id: str, learner_id: str) -> dict:
    if programme_id.startswith("do_"):
        payload = public_course(programme_id)
        stored = sqlite_db.get_course_progress(learner_id, programme_id)
        payload["progress"] = stored or {
            "programme_id": programme_id,
            "correct_count": 0,
            "question_count": len(payload["questions"]),
            "passed": False,
            "status": "Not started",
            "updated_at": None,
        }
        return payload
    programme, questions = _questions(programme_id)
    stored = sqlite_db.get_course_progress(learner_id, programme_id)
    return {
        **public_programme(programme),
        "lessons": [item.lesson for item in questions],
        "questions": [
            {"id": item.id, "prompt": item.prompt, "options": list(item.options)}
            for item in questions
        ],
        "pass_rule": "At least 2 of 3 answers must be correct.",
        "progress": stored
        or {
            "programme_id": programme_id,
            "correct_count": 0,
            "question_count": len(questions),
            "passed": False,
            "status": "Not started",
            "updated_at": None,
        },
    }


def progress_for_learner(learner_id: str) -> dict:
    rows = sqlite_db.list_course_progress(learner_id)
    return {"learner_id": learner_id, "courses": rows}


def submit_course(programme_id: str, learner_id: str, answers: list[dict]) -> dict:
    if programme_id.startswith("do_"):
        questions = questions_for(programme_id)
        title = public_course(programme_id)["title"]
        by_id = {item["id"]: item for item in questions}
        incoming = {item["question_id"]: item["selected_answer"] for item in answers}
        if set(incoming) != set(by_id):
            raise HTTPException(status_code=422, detail="Answer every question in the course.")
        reviews = []
        correct = 0
        for item in questions:
            chosen = incoming[item["id"]]
            if chosen not in item["options"]:
                raise HTTPException(status_code=422, detail="Choose one of the listed answers.")
            ok = chosen == item["answer"]
            correct += int(ok)
            reviews.append({"question_id": item["id"], "correct": ok})
        total = len(questions)
        passed_now = level_met(correct, total)
        stored = sqlite_db.save_course_progress(
            learner_id,
            programme_id,
            correct,
            total,
            passed_now,
            datetime.now(UTC).isoformat(),
        )
        return {
            "programme_id": programme_id,
            "title": title,
            "correct_count": correct,
            "question_count": total,
            "score_percent": display_percent(correct, total),
            "passed_this_attempt": passed_now,
            "status": stored["status"],
            "reviews": reviews,
        }
    programme, questions = _questions(programme_id)
    by_id = {item.id: item for item in questions}
    incoming = {item["question_id"]: item["selected_answer"] for item in answers}
    if set(incoming) != set(by_id):
        raise HTTPException(status_code=422, detail="Answer every question in the course.")
    reviews = []
    correct = 0
    for item in questions:
        chosen = incoming[item.id]
        if chosen not in item.options:
            raise HTTPException(status_code=422, detail="Choose one of the listed answers.")
        ok = chosen == item.options[item.correct_index]
        correct += int(ok)
        reviews.append({"question_id": item.id, "correct": ok})
    total = len(questions)
    passed_now = level_met(correct, total)
    stored = sqlite_db.save_course_progress(
        learner_id,
        programme_id,
        correct,
        total,
        passed_now,
        datetime.now(UTC).isoformat(),
    )
    return {
        "programme_id": programme.id,
        "title": programme.title,
        "correct_count": correct,
        "question_count": total,
        "score_percent": display_percent(correct, total),
        "passed_this_attempt": passed_now,
        "status": stored["status"],
        "reviews": reviews,
    }
