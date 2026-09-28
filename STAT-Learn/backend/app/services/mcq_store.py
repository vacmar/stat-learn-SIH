"""Draft MCQ store. Memory plus a Redis snapshot. Does not touch learner scores."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.core.cache import get_redis_client
from app.data.sampling_note import CHUNK_BY_ID, DOCUMENT, KNOWN_COMPETENCIES
from app.services.mcq_generation import normalize_stem

logger = logging.getLogger(__name__)

_QUESTIONS: dict[str, dict[str, Any]] = {}
_AUDIT: list[dict[str, Any]] = []
_redis_disabled = False
ACTOR = "training-admin"


def reset_memory() -> None:
    global _redis_disabled
    _QUESTIONS.clear()
    _AUDIT.clear()
    _redis_disabled = False


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _persist_question(item: dict[str, Any]) -> None:
    global _redis_disabled
    _QUESTIONS[item["id"]] = item
    if _redis_disabled:
        return
    try:
        get_redis_client().set(f"statlearn:mcq:{item['id']}", json.dumps(item), ex=60 * 60 * 24 * 14)
    except Exception as exc:
        _redis_disabled = True
        logger.warning("MCQ snapshot skipped: %s", exc)


def _duplicate(stem: str) -> bool:
    key = normalize_stem(stem)
    return any(
        normalize_stem(item["question"]) == key and item["status"] in {"DRAFT", "APPROVED"}
        for item in _QUESTIONS.values()
    )


def evidence_for(chunk_ids: list[str]) -> list[dict[str, str]]:
    rows = []
    for chunk_id in chunk_ids:
        chunk = CHUNK_BY_ID[chunk_id]
        rows.append(
            {
                "chunk_id": chunk.id,
                "section": chunk.section,
                "text": chunk.text,
                "document_title": DOCUMENT.title,
                "source": DOCUMENT.source_label,
            }
        )
    return rows


def create_question(candidate: dict) -> dict:
    if _duplicate(candidate["question"]):
        raise ValueError("Duplicate question")
    name, domain = KNOWN_COMPETENCIES[candidate["competency_id"]]
    item = {
        "id": uuid4().hex,
        "document_id": DOCUMENT.id,
        "source_chunk_ids": list(candidate["source_chunk_ids"]),
        "question": candidate["question"],
        "options": list(candidate["options"]),
        "correct_option": candidate["correct_option"],
        "explanation": candidate["explanation"],
        "competency_id": candidate["competency_id"],
        "competency": name,
        "domain": domain,
        "target_level": candidate["target_level"],
        "status": "DRAFT",
        "origin": candidate["origin"],
        "created_at": _now(),
        "approved_at": None,
        "evidence": evidence_for(candidate["source_chunk_ids"]),
    }
    _persist_question(item)
    return item


def get_question(question_id: str) -> dict | None:
    return _QUESTIONS.get(question_id)


def list_questions(status: str | None = None) -> list[dict]:
    rows = list(_QUESTIONS.values())
    if status:
        rows = [item for item in rows if item["status"] == status]
    rows.sort(key=lambda item: item["created_at"])
    return rows


def transition(question_id: str, action: str) -> dict:
    item = _QUESTIONS.get(question_id)
    if not item:
        raise KeyError(question_id)
    if item["status"] != "DRAFT":
        raise PermissionError(item["status"])
    if action not in {"approve", "reject"}:
        raise PermissionError(item["status"])
    previous = item["status"]
    updated = {
        **item,
        "status": "APPROVED" if action == "approve" else "REJECTED",
        "approved_at": _now() if action == "approve" else None,
    }
    _persist_question(updated)
    _AUDIT.append(
        {
            "question_id": question_id,
            "action": action,
            "actor": ACTOR,
            "timestamp": _now(),
            "previous_status": previous,
        }
    )
    return updated


def audit_for(question_id: str) -> list[dict]:
    return [row for row in _AUDIT if row["question_id"] == question_id]


def counts() -> dict:
    today = _now()[:10]
    rows = list(_QUESTIONS.values())
    return {
        "learning_materials": 1,
        "draft_mcqs": sum(1 for item in rows if item["status"] == "DRAFT"),
        "awaiting_review": sum(1 for item in rows if item["status"] == "DRAFT"),
        "approved_questions": sum(1 for item in rows if item["status"] == "APPROVED"),
        "rejected_questions": sum(1 for item in rows if item["status"] == "REJECTED"),
        "generated_today": sum(1 for item in rows if str(item["created_at"]).startswith(today)),
    }


def public_question(item: dict) -> dict:
    return {
        "id": item["id"],
        "question": item["question"],
        "options": item["options"],
        "correct_option": item["correct_option"],
        "explanation": item["explanation"],
        "competency": item["competency"],
        "competency_id": item["competency_id"],
        "domain": item["domain"],
        "target_level": item["target_level"],
        "status": item["status"],
        "origin": item["origin"],
        "badge": "AI generated" if item["origin"] == "model" else "Demo-generated draft",
        "source": DOCUMENT.source_label,
        "document_title": DOCUMENT.title,
        "created_at": item["created_at"],
        "approved_at": item["approved_at"],
        "evidence": item["evidence"],
    }
