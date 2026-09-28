"""Conversational lesson tutor — ChatGPT-style, scoped to the active path node."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.core.llm import get_llm
from app.models.structured import ChatRequest, ChatResponse
from app.personas.prompts import LESSON_CHAT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def _lesson_state_block(req: ChatRequest) -> str:
    ctx = req.lesson_context or {}
    current = ctx.get("current_node_title") or req.node_id or "Current lesson"
    upcoming = ctx.get("upcoming_nodes") or []
    completed = ctx.get("completed_nodes") or []
    goal = ctx.get("goal") or "their learning goal"
    lines = [
        f"Learner ID: {req.learner_id}",
        f"Goal: {goal}",
        f"CURRENT NODE (teach only this): {current}",
        f"Completed nodes: {', '.join(completed) if completed else 'none yet'}",
        f"Upcoming nodes (defer these topics): {', '.join(upcoming) if upcoming else 'none listed'}",
        f"Chat turns so far (approx): {len(req.history or [])}",
    ]
    return "\n".join(lines)


def _extract_json(text: str) -> dict[str, Any] | None:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except (json.JSONDecodeError, TypeError):
            return None
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except (json.JSONDecodeError, TypeError):
            return None
    return None


def _heuristic_ready(req: ChatRequest) -> bool:
    """Fallback when the model forgets the ready flag."""
    history = req.history or []
    if len(history) < 3:
        return False
    last_user = (req.message or "").strip().lower()
    affirm = (
        "no doubt",
        "no doubts",
        "i understand",
        "understood",
        "got it",
        "makes sense",
        "clear now",
        "yes i get",
        "i'm good",
        "im good",
        "ready to move",
        "can we finish",
        "complete",
    )
    return any(a in last_user for a in affirm)


def _normalize_assistant_text(
    raw: str, parsed: dict[str, Any] | None
) -> tuple[str, bool, str]:
    """Always return learner-facing prose, never raw JSON."""
    if parsed and parsed.get("message") is not None:
        text = str(parsed.get("message") or "").strip()
        # If model nested JSON again inside message, unwrap once more
        nested = _extract_json(text)
        if nested and nested.get("message"):
            text = str(nested.get("message") or "").strip()
            ready = bool(
                nested.get(
                    "node_ready_to_complete", parsed.get("node_ready_to_complete")
                )
            )
            reason = str(nested.get("ready_reason") or parsed.get("ready_reason") or "")
            return text, ready, reason
        ready = bool(parsed.get("node_ready_to_complete"))
        reason = str(parsed.get("ready_reason") or "")
        return text, ready, reason

    # Raw body looked like JSON but failed parse — strip braces heuristically
    stripped = raw.strip()
    if stripped.startswith("{") and '"message"' in stripped:
        m = re.search(r'"message"\s*:\s*"(.*)"\s*,\s*"node_ready', stripped, re.DOTALL)
        if not m:
            m = re.search(r'"message"\s*:\s*"(.*?)"\s*}', stripped, re.DOTALL)
        if m:
            try:
                text = json.loads(f'"{m.group(1)}"')
            except json.JSONDecodeError:
                text = m.group(1).replace('\\"', '"').replace("\\n", "\n")
            ready = '"node_ready_to_complete": true' in stripped.lower().replace(
                " ", ""
            )
            return text.strip(), ready, "heuristic_unwrap"
    return (
        stripped or "I'm here — tell me what part you'd like to go over again.",
        False,
        "plain_text_reply",
    )


async def run_lesson_chat(req: ChatRequest) -> ChatResponse:
    """Reply in a live conversational lesson, grounded to the current node."""
    system = (
        f"{LESSON_CHAT_SYSTEM_PROMPT}\n\n"
        f"[LESSON SCOPE — AUTHORITATIVE]\n{_lesson_state_block(req)}"
    )
    messages: list[Any] = [SystemMessage(content=system)]

    for turn in (req.history or [])[-12:]:
        role = (turn.get("role") or "").lower()
        content = (turn.get("content") or "").strip()
        if not content:
            continue
        # Never feed raw JSON blobs back into history
        if content.lstrip().startswith("{") and '"message"' in content:
            nested = _extract_json(content)
            if nested and nested.get("message"):
                content = str(nested["message"])
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))

    messages.append(HumanMessage(content=req.message))

    try:
        llm = get_llm(temperature=0.4)
        response = await llm.ainvoke(messages)
        raw = str(response.content or "").strip()
        parsed = _extract_json(raw) if raw else None
        text, ready, reason = _normalize_assistant_text(raw, parsed)

        if not ready:
            ready = _heuristic_ready(req)
            if ready and not reason:
                reason = "learner_affirmed_understanding"

        # Never mark ready on a cold start / first opener
        if len(req.history or []) < 2:
            ready = False

        return ChatResponse(
            message=text,
            persona="tutor",
            structured={
                "content": text,
                "concept_focus": (req.lesson_context or {}).get(
                    "current_node_title", "Current lesson"
                ),
                "mode": "lesson_chat",
                "node_ready_to_complete": ready,
                "ready_reason": reason,
            },
            tool_calls=[],
        )
    except Exception as e:
        logger.warning("Lesson chat LLM failed: %s", e)
        current = (req.lesson_context or {}).get("current_node_title") or "this lesson"
        return ChatResponse(
            message=(
                f"I hit a temporary snag talking to the model. "
                f"While we reconnect, what specifically about {current} are you stuck on?"
            ),
            persona="tutor",
            structured={
                "content": "",
                "mode": "lesson_chat_fallback",
                "node_ready_to_complete": False,
            },
            tool_calls=[],
        )
