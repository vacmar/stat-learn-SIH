"""In-memory attempt store with a Redis snapshot. Not an Exasol migration."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.core.cache import get_redis_client
from app.data.diagnostic_seed import (
    ASSESSMENT_ID,
    QUESTIONS,
    QUESTION_BY_ID,
    TARGET_BY_ID,
)
from app.services.competency_engine import score_attempt

logger = logging.getLogger(__name__)

_ATTEMPTS: dict[str, dict[str, Any]] = {}
_TTL_SECONDS = 60 * 60 * 24 * 14
_redis_disabled = False


def reset_memory() -> None:
    global _redis_disabled
    _ATTEMPTS.clear()
    _redis_disabled = False


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _key(attempt_id: str) -> str:
    return f"statlearn:competency:attempt:{attempt_id}"


def _learner_key(learner_id: str) -> str:
    return f"statlearn:competency:learner:{learner_id}"


def _persist(attempt: dict[str, Any]) -> None:
    global _redis_disabled
    _ATTEMPTS[attempt["attempt_id"]] = attempt
    if _redis_disabled:
        return
    try:
        cache = get_redis_client()
        cache.set(_key(attempt["attempt_id"]), json.dumps(attempt), ex=_TTL_SECONDS)
        cache.sadd(_learner_key(attempt["learner_id"]), attempt["attempt_id"])
        cache.expire(_learner_key(attempt["learner_id"]), _TTL_SECONDS)
    except Exception as exc:
        _redis_disabled = True
        logger.warning("Competency snapshot skipped: %s", exc)


def get_attempt(attempt_id: str) -> dict[str, Any] | None:
    global _redis_disabled
    if attempt_id in _ATTEMPTS:
        return _ATTEMPTS[attempt_id]
    if _redis_disabled:
        return None
    try:
        raw = get_redis_client().get(_key(attempt_id))
    except Exception:
        _redis_disabled = True
        raw = None
    if not raw:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    attempt = json.loads(raw)
    _ATTEMPTS[attempt_id] = attempt
    return attempt


def list_attempt_ids(learner_id: str) -> list[str]:
    global _redis_disabled
    ids = {item["attempt_id"] for item in _ATTEMPTS.values() if item["learner_id"] == learner_id}
    if _redis_disabled:
        return list(ids)
    try:
        cached = get_redis_client().smembers(_learner_key(learner_id))
        for attempt_id in cached:
            if isinstance(attempt_id, bytes):
                attempt_id = attempt_id.decode("utf-8")
            ids.add(str(attempt_id))
    except Exception:
        _redis_disabled = True
    return list(ids)


def create_attempt(learner_id: str) -> dict[str, Any]:
    attempt = {
        "attempt_id": uuid4().hex,
        "learner_id": learner_id,
        "assessment_id": ASSESSMENT_ID,
        "started_at": _now(),
        "completed_at": None,
        "status": "in_progress",
        "answers": {},
        "result": None,
    }
    _persist(attempt)
    return attempt


def record_answer(attempt: dict[str, Any], question_id: str, selected_answer: str) -> dict[str, Any]:
    answers = dict(attempt["answers"])
    answers[question_id] = selected_answer
    updated = {**attempt, "answers": answers}
    _persist(updated)
    return updated


def complete_attempt(attempt: dict[str, Any]) -> dict[str, Any]:
    questions = []
    for item in QUESTIONS:
        questions.append(
            {
                "id": item.id,
                "competency_id": item.competency_id,
                "name": item.competency_name,
                "domain": item.domain,
                "level": item.level,
                "topic": item.topic,
                "correct_answer": item.correct_answer,
            }
        )
    targets = [
        {
            "competency_id": target.competency_id,
            "name": target.name,
            "domain": target.domain,
            "target_level": target.target_level,
        }
        for target in TARGET_BY_ID.values()
    ]
    result = score_attempt(questions, dict(attempt["answers"]), targets)
    result["attempt_id"] = attempt["attempt_id"]
    result["assessment_id"] = attempt["assessment_id"]
    result["learner_id"] = attempt["learner_id"]
    completed = {
        **attempt,
        "status": "completed",
        "completed_at": _now(),
        "result": result,
    }
    _persist(completed)
    return completed


def question_or_none(question_id: str):
    return QUESTION_BY_ID.get(question_id)


def latest_completed(learner_id: str) -> dict[str, Any] | None:
    completed = []
    for attempt_id in list_attempt_ids(learner_id):
        attempt = get_attempt(attempt_id)
        if attempt and attempt["status"] == "completed" and attempt.get("result"):
            completed.append(attempt)
    if not completed:
        return None
    completed.sort(key=lambda item: item.get("completed_at") or "", reverse=True)
    return completed[0]


def history_for(learner_id: str) -> list[dict[str, Any]]:
    rows = []
    for attempt_id in list_attempt_ids(learner_id):
        attempt = get_attempt(attempt_id)
        if not attempt or attempt["status"] != "completed":
            continue
        result = attempt.get("result") or {}
        rows.append(
            {
                "attempt_id": attempt["attempt_id"],
                "completed_at": attempt.get("completed_at"),
                "score": result.get("overall_score_percent"),
                "status": attempt["status"],
            }
        )
    rows.sort(key=lambda item: item.get("completed_at") or "", reverse=True)
    return rows
