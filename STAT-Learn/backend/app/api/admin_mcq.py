"""Training Admin routes for source-grounded draft review."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.data.sampling_note import public_document
from app.services import mcq_store
from app.services.mcq_generation import (
    UNAVAILABLE,
    GenerationError,
    call_model,
    candidates_from_model,
    demo_candidate,
    model_available,
    prompt_for,
    select_context,
)

router = APIRouter(prefix="/admin", tags=["MCQ review"])
ADMIN_HEADER = "X-Statlearn-Demo-Actor"
ADMIN_TOKEN = "training-admin"


class GenerateBody(BaseModel):
    document_id: str
    competency_id: str
    target_level: str
    count: int = Field(default=1, ge=1, le=3)


def require_admin(request: Request) -> str:
    if request.headers.get(ADMIN_HEADER) != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Training Admin session required")
    return ADMIN_TOKEN


def _store_candidates(candidates: list[dict]) -> list[dict]:
    created = []
    try:
        for candidate in candidates:
            created.append(mcq_store.public_question(mcq_store.create_question(candidate)))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail="Duplicate question") from exc
    return created


@router.get("/materials")
def materials(request: Request):
    require_admin(request)
    return {"documents": [public_document()]}


@router.get("/overview")
def overview(request: Request):
    require_admin(request)
    return mcq_store.counts()


@router.post("/mcq/generate")
def generate(body: GenerateBody, request: Request):
    require_admin(request)
    if not model_available():
        raise HTTPException(status_code=503, detail=UNAVAILABLE)
    try:
        chunks = select_context(body.document_id, body.competency_id)
        payloads = []
        for _ in range(body.count):
            try:
                payloads.append(call_model(prompt_for(chunks, body.competency_id, body.target_level)))
            except Exception as exc:
                raise HTTPException(status_code=503, detail=UNAVAILABLE) from exc
        candidates = candidates_from_model(payloads, chunks, body.competency_id, body.target_level)
    except GenerationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    return {"drafts": _store_candidates(candidates)}


@router.post("/mcq/demo-draft")
def demo_draft(body: GenerateBody, request: Request):
    require_admin(request)
    try:
        chunks = select_context(body.document_id, body.competency_id)
    except GenerationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    candidates = []
    for index in range(body.count):
        chunk = chunks[index % len(chunks)]
        candidates.append(demo_candidate(chunk, body.competency_id, body.target_level))
    try:
        return {"drafts": _store_candidates(candidates)}
    except HTTPException:
        raise


@router.get("/mcq-review")
def review_queue(request: Request):
    require_admin(request)
    return {"drafts": [mcq_store.public_question(item) for item in mcq_store.list_questions("DRAFT")]}


@router.post("/mcq/{question_id}/approve")
def approve(question_id: str, request: Request):
    require_admin(request)
    return _transition(question_id, "approve")


@router.post("/mcq/{question_id}/reject")
def reject(question_id: str, request: Request):
    require_admin(request)
    return _transition(question_id, "reject")


def _transition(question_id: str, action: str) -> dict:
    try:
        updated = mcq_store.transition(question_id, action)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Question not found") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail="Question has already been reviewed") from exc
    return {"question": mcq_store.public_question(updated), "audit": mcq_store.audit_for(question_id)}


@router.get("/question-bank")
def question_bank(request: Request, domain: str | None = None, level: str | None = None):
    require_admin(request)
    rows = []
    for item in mcq_store.list_questions("APPROVED"):
        if domain and domain != "All" and item["domain"] != domain:
            continue
        if level and level != "All" and item["target_level"] != level:
            continue
        rows.append(mcq_store.public_question(item))
    return {"questions": rows}
