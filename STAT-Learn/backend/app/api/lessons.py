"""Per-node lesson chat + practice notes for the interactive tutor."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.auth import get_current_learner
from app.models.domain import Learner
from app.repository import state_repo

router = APIRouter(prefix="/lessons", tags=["Lessons"])


class LessonMessage(BaseModel):
    role: str
    content: str


class NotesPayload(BaseModel):
    practice_notes: str = Field(default="")


class MessagesReplacePayload(BaseModel):
    """Replace or append the full visible chat transcript for a node."""

    messages: list[LessonMessage] = Field(default_factory=list)
    replace: bool = True


class ReadyPayload(BaseModel):
    ai_ready: bool = False
    ready_reason: str | None = None


def _unwrap_assistant_content(content: str) -> str:
    """Strip accidental JSON wrappers so UI never stores raw model envelopes."""
    text = (content or "").strip()
    if not (text.startswith("{") and '"message"' in text):
        return content
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict) and parsed.get("message") is not None:
            inner = str(parsed["message"]).strip()
            if inner.startswith("{") and '"message"' in inner:
                return _unwrap_assistant_content(inner)
            return inner
    except (json.JSONDecodeError, TypeError):
        pass
    m = re.search(r'"message"\s*:\s*"(.*)"\s*,\s*"node_ready', text, re.DOTALL)
    if not m:
        m = re.search(r'"message"\s*:\s*"(.*?)"\s*}', text, re.DOTALL)
    if m:
        try:
            return json.loads(f'"{m.group(1)}"')
        except json.JSONDecodeError:
            return m.group(1).replace('\\"', '"').replace("\\n", "\n")
    return content


@router.get("/me/{node_id}/session")
def get_lesson_session(node_id: str, learner: Learner = Depends(get_current_learner)):
    # Hydrate Redis/Exasol → RAM first, then read
    notes = state_repo.get_lesson_notes(learner.learner_id, node_id)
    meta = state_repo.get_lesson_meta(learner.learner_id, node_id)
    conv_id = state_repo.lesson_conversation_id(learner.learner_id, node_id)
    messages = state_repo.get_conversation(conv_id)
    cleaned = []
    for m in messages:
        role = m.get("role")
        content = m.get("content") or ""
        if role == "assistant":
            content = _unwrap_assistant_content(content)
        cleaned.append({**m, "content": content})
    return {
        "node_id": node_id,
        "conversation_id": conv_id,
        "messages": cleaned,
        "practice_notes": notes,
        "ai_ready": bool(meta.get("ai_ready")),
        "ready_reason": meta.get("ready_reason"),
    }


@router.put("/me/{node_id}/notes")
def save_lesson_notes(
    node_id: str,
    payload: NotesPayload,
    learner: Learner = Depends(get_current_learner),
):
    saved = state_repo.save_lesson_notes(
        learner.learner_id, node_id, payload.practice_notes or ""
    )
    return {"node_id": node_id, "practice_notes": saved, "saved": True}


@router.put("/me/{node_id}/ready")
def save_lesson_ready(
    node_id: str,
    payload: ReadyPayload,
    learner: Learner = Depends(get_current_learner),
):
    meta = state_repo.save_lesson_meta(
        learner.learner_id,
        node_id,
        {
            "ai_ready": payload.ai_ready,
            "ready_reason": payload.ready_reason,
            "updated_at": datetime.now(UTC).isoformat(),
        },
    )
    return {"node_id": node_id, **meta}


@router.post("/me/{node_id}/messages")
def save_lesson_messages(
    node_id: str,
    payload: MessagesReplacePayload,
    learner: Learner = Depends(get_current_learner),
):
    now = datetime.now(UTC).isoformat()
    msgs = []
    for msg in payload.messages:
        content = msg.content or ""
        if msg.role == "assistant":
            content = _unwrap_assistant_content(content)
        msgs.append({"role": msg.role, "content": content, "created_at": now})

    if payload.replace:
        cleaned = state_repo.replace_lesson_messages(learner.learner_id, node_id, msgs)
    else:
        conv_id = state_repo.lesson_conversation_id(learner.learner_id, node_id)
        existing = list(state_repo.get_conversation(conv_id))
        cleaned = state_repo.replace_lesson_messages(
            learner.learner_id, node_id, existing + msgs
        )

    return {
        "node_id": node_id,
        "conversation_id": state_repo.lesson_conversation_id(
            learner.learner_id, node_id
        ),
        "message_count": len(cleaned),
    }
