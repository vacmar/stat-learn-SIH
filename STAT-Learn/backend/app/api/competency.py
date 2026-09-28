"""Competency assessment and profile routes. Scoring stays in competency_engine."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from app.api.auth import SESSION_COOKIE_NAME
from app.core.cache import get_redis_client
from app.data.diagnostic_seed import (
    ASSESSMENT_ID,
    DEMO_LEARNER_HEADER,
    DEMO_LEARNER_ID,
    DEMO_LEARNER_TOKEN,
    QUESTIONS,
    TARGET_BY_ID,
    public_assessment,
)
from app.repository import state_repo
from app.services import competency_store
from app.services.course_study import course_for_learner, progress_for_learner, submit_course
from app.services.recommendation_engine import (
    NO_ASSESSMENT_MESSAGE,
    build_pathway,
    catalogue_payload,
    recommend_for_attempt,
)

assessment_router = APIRouter(prefix="/assessments", tags=["Competency assessment"])
competency_router = APIRouter(prefix="/competencies", tags=["Competencies"])


class AnswerBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question_id: str
    selected_answer: str


class CourseSubmitBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answers: list[AnswerBody]


def resolve_learner_id(request: Request) -> str:
    """Cookie session wins. Otherwise only the seeded screening token is accepted."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id:
        try:
            cache = get_redis_client()
            account_id = cache.get(f"session:{session_id}")
            if isinstance(account_id, bytes):
                account_id = account_id.decode("utf-8")
            if account_id:
                learner = state_repo.get_learner_by_account(str(account_id))
                if learner:
                    return learner.learner_id
        except Exception:
            pass
    token = request.headers.get(DEMO_LEARNER_HEADER)
    if token == DEMO_LEARNER_TOKEN:
        return DEMO_LEARNER_ID
    raise HTTPException(status_code=401, detail="Not authenticated")


def _owned_attempt(attempt_id: str, learner_id: str) -> dict:
    attempt = competency_store.get_attempt(attempt_id)
    if not attempt or attempt["assessment_id"] != ASSESSMENT_ID:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if attempt["learner_id"] != learner_id:
        raise HTTPException(status_code=403, detail="Attempt belongs to another learner")
    return attempt


def _ensure_open(attempt: dict) -> None:
    if attempt["status"] == "completed":
        raise HTTPException(status_code=409, detail="Attempt is already completed")


@assessment_router.get("/diagnostic")
def get_diagnostic(request: Request):
    resolve_learner_id(request)
    return public_assessment()


@assessment_router.post("/attempts")
def create_attempt(request: Request):
    learner_id = resolve_learner_id(request)
    attempt = competency_store.create_attempt(learner_id)
    return {
        "attempt_id": attempt["attempt_id"],
        "learner_id": attempt["learner_id"],
        "assessment_id": attempt["assessment_id"],
        "started_at": attempt["started_at"],
        "completed_at": attempt["completed_at"],
        "status": attempt["status"],
    }


@assessment_router.get("/attempts/{attempt_id}")
def get_attempt(attempt_id: str, request: Request):
    learner_id = resolve_learner_id(request)
    attempt = _owned_attempt(attempt_id, learner_id)
    return {
        "attempt_id": attempt["attempt_id"],
        "learner_id": attempt["learner_id"],
        "assessment_id": attempt["assessment_id"],
        "started_at": attempt["started_at"],
        "completed_at": attempt["completed_at"],
        "status": attempt["status"],
        "answers": [
            {"question_id": question_id, "selected_answer": selected}
            for question_id, selected in attempt["answers"].items()
        ],
    }


@assessment_router.post("/attempts/{attempt_id}/answers")
def submit_answer(attempt_id: str, body: AnswerBody, request: Request):
    learner_id = resolve_learner_id(request)
    attempt = _owned_attempt(attempt_id, learner_id)
    _ensure_open(attempt)
    question = competency_store.question_or_none(body.question_id)
    if question is None:
        raise HTTPException(status_code=422, detail="Question is not part of this assessment")
    if body.selected_answer not in question.options:
        raise HTTPException(status_code=422, detail="Selected answer is not a valid option")
    if body.question_id in attempt["answers"]:
        raise HTTPException(status_code=409, detail="This question already has an answer")
    updated = competency_store.record_answer(attempt, body.question_id, body.selected_answer)
    return {
        "attempt_id": updated["attempt_id"],
        "question_id": body.question_id,
        "status": updated["status"],
    }


@assessment_router.post("/attempts/{attempt_id}/complete")
def complete_attempt(attempt_id: str, request: Request):
    learner_id = resolve_learner_id(request)
    attempt = _owned_attempt(attempt_id, learner_id)
    _ensure_open(attempt)
    missing = [item.id for item in QUESTIONS if item.id not in attempt["answers"]]
    if missing:
        raise HTTPException(status_code=422, detail="Required answers are missing")
    completed = competency_store.complete_attempt(attempt)
    return completed["result"]


@assessment_router.get("/attempts/{attempt_id}/result")
def get_result(attempt_id: str, request: Request):
    learner_id = resolve_learner_id(request)
    attempt = _owned_attempt(attempt_id, learner_id)
    if attempt["status"] != "completed" or not attempt.get("result"):
        raise HTTPException(status_code=409, detail="Result is not available until the attempt is completed")
    return attempt["result"]


@competency_router.get("")
def list_competencies(request: Request):
    resolve_learner_id(request)
    return {
        "competencies": [
            {
                "competency_id": item.competency_id,
                "name": item.name,
                "domain": item.domain,
                "domain_label": item.domain_label,
                "target_level": f"L{item.target_level}",
            }
            for item in TARGET_BY_ID.values()
        ]
    }


@competency_router.get("/profile")
def get_profile(request: Request):
    learner_id = resolve_learner_id(request)
    attempt = competency_store.latest_completed(learner_id)
    if not attempt:
        return {
            "learner_id": learner_id,
            "assessed": False,
            "overall_score_percent": None,
            "competencies_assessed": 0,
            "priority_gap_count": 0,
            "domain_readiness": [],
            "competencies": [],
            "attempt_id": None,
            "completed_at": None,
        }
    result = attempt["result"]
    return {
        "learner_id": learner_id,
        "assessed": True,
        "overall_score_percent": result["overall_score_percent"],
        "competencies_assessed": result["competencies_assessed"],
        "priority_gap_count": result["priority_gap_count"],
        "domain_readiness": result["domain_readiness"],
        "competencies": result["competencies"],
        "attempt_id": attempt["attempt_id"],
        "completed_at": attempt["completed_at"],
    }


@competency_router.get("/gaps")
def list_gaps(request: Request):
    learner_id = resolve_learner_id(request)
    attempt = competency_store.latest_completed(learner_id)
    if not attempt:
        return {"learner_id": learner_id, "attempt_id": None, "gaps": []}
    gaps = []
    for row in attempt["result"]["competencies"]:
        gaps.append({**row, "assessment_attempt_id": attempt["attempt_id"]})
    return {
        "learner_id": learner_id,
        "attempt_id": attempt["attempt_id"],
        "completed_at": attempt["completed_at"],
        "assessment_title": "Diagnostic Competency Assessment",
        "gaps": gaps,
    }


@competency_router.get("/gaps/{competency_id}")
def get_gap(competency_id: str, request: Request):
    learner_id = resolve_learner_id(request)
    attempt = competency_store.latest_completed(learner_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="No completed assessment")
    for row in attempt["result"]["competencies"]:
        if row["competency_id"] == competency_id:
            return {
                **row,
                "learner_id": learner_id,
                "assessment_attempt_id": attempt["attempt_id"],
                "assessment_title": "Diagnostic Competency Assessment",
                "completed_at": attempt["completed_at"],
            }
    raise HTTPException(status_code=404, detail="Competency result not found")


@competency_router.get("/recommendations")
def recommendations(request: Request):
    learner_id = resolve_learner_id(request)
    payload = recommend_for_attempt(competency_store.latest_completed(learner_id))
    payload["learner_id"] = learner_id
    if payload["message"] is None and payload["recommendations"]:
        payload["message"] = None
    return payload


@competency_router.get("/pathway")
def pathway(request: Request):
    learner_id = resolve_learner_id(request)
    attempt = competency_store.latest_completed(learner_id)
    recommended = recommend_for_attempt(attempt)
    recommended["learner_id"] = learner_id
    sequenced = build_pathway(recommended)
    return {
        "learner_id": learner_id,
        "assessment_attempt_id": recommended["assessment_attempt_id"],
        "message": recommended["message"] or (
            NO_ASSESSMENT_MESSAGE if not attempt else sequenced.get("message")
        ),
        "journeys": sequenced["journeys"],
    }


@competency_router.get("/catalogue")
def catalogue(request: Request):
    resolve_learner_id(request)
    return catalogue_payload()


@competency_router.get("/course-progress")
def course_progress(request: Request):
    return progress_for_learner(resolve_learner_id(request))


@competency_router.get("/catalogue/{programme_id}")
def course_detail(programme_id: str, request: Request):
    return course_for_learner(programme_id, resolve_learner_id(request))


@competency_router.post("/catalogue/{programme_id}/submit")
def course_submit(programme_id: str, body: CourseSubmitBody, request: Request):
    return submit_course(
        programme_id,
        resolve_learner_id(request),
        [item.model_dump() for item in body.answers],
    )


@competency_router.get("/history")
def history(request: Request):
    learner_id = resolve_learner_id(request)
    return {"learner_id": learner_id, "attempts": competency_store.history_for(learner_id)}
