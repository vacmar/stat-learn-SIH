"""Candidate MCQ generation. Does not score learners or publish questions."""

from __future__ import annotations

import json
import os
import re

from app.data.sampling_note import (
    CHUNK_BY_ID,
    DOCUMENT,
    KNOWN_COMPETENCIES,
    SourceChunk,
    chunks_for_competency,
)

UNAVAILABLE = "AI generation unavailable. No draft was created."
LEVELS = {"L1", "L2", "L3", "L4", "L5"}


class GenerationError(Exception):
    def __init__(self, message: str, status_code: int = 422) -> None:
        super().__init__(message)
        self.status_code = status_code


def normalize_stem(text: str) -> str:
    lowered = text.lower()
    cleaned = re.sub(r"[^a-z0-9\s]", " ", lowered)
    return re.sub(r"\s+", " ", cleaned).strip()


def validate_candidate(payload: dict, allowed_chunk_ids: set[str], competency_id: str, target_level: str) -> dict:
    question = str(payload.get("question") or "").strip()
    options = payload.get("options")
    correct = str(payload.get("correct_option") or "").strip()
    explanation = str(payload.get("explanation") or "").strip()
    cited = payload.get("source_chunk_ids") or []
    if not question:
        raise GenerationError("Question is missing")
    if not isinstance(options, list) or len(options) != 4:
        raise GenerationError("Exactly four options are required")
    cleaned = [str(option).strip() for option in options]
    if any(not option for option in cleaned):
        raise GenerationError("Options must be non-empty")
    if correct not in cleaned:
        raise GenerationError("Correct option is not one of the options")
    if not explanation:
        raise GenerationError("Explanation is missing")
    if competency_id not in KNOWN_COMPETENCIES:
        raise GenerationError("Competency is not recognised")
    if target_level not in LEVELS:
        raise GenerationError("Target level is not valid")
    if not isinstance(cited, list) or not cited:
        raise GenerationError("Source evidence is missing")
    chunk_ids = [str(item) for item in cited]
    if any(chunk_id not in allowed_chunk_ids or chunk_id not in CHUNK_BY_ID for chunk_id in chunk_ids):
        raise GenerationError("Source chunk is missing")
    return {
        "question": question,
        "options": cleaned,
        "correct_option": correct,
        "explanation": explanation,
        "source_chunk_ids": chunk_ids,
        "competency_id": competency_id,
        "target_level": target_level,
    }


def select_context(document_id: str, competency_id: str) -> list[SourceChunk]:
    if document_id != DOCUMENT.id:
        raise GenerationError("Source document is missing", 404)
    if competency_id not in KNOWN_COMPETENCIES:
        raise GenerationError("Competency is not recognised")
    return chunks_for_competency(competency_id)


def prompt_for(chunks: list[SourceChunk], competency_id: str, target_level: str) -> str:
    name = KNOWN_COMPETENCIES[competency_id][0]
    blocks = "\n\n".join(f"Chunk {chunk.id} ({chunk.section}):\n{chunk.text}" for chunk in chunks)
    return (
        "You draft one candidate multiple-choice question using only the source chunks below. "
        "Do not add facts that are not in the chunks. Return JSON with keys question, options "
        "(exactly four strings), correct_option (one of the options), explanation, and "
        f"source_chunk_ids. Competency label: {name}. Target level: {target_level}. "
        "This draft is not a learner score and must not be treated as published.\n\n"
        f"Document: {DOCUMENT.title} ({DOCUMENT.source_label})\n\n{blocks}"
    )


def parse_model_json(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise GenerationError("Malformed model output") from exc
    if not isinstance(parsed, dict):
        raise GenerationError("Malformed model output")
    return parsed


def model_available() -> bool:
    provider = os.getenv("LLM_PROVIDER", "mock").strip().lower()
    if provider in {"", "mock"}:
        return False
    key_name = {
        "groq": "GROQ_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "huggingface": "HUGGINGFACE_API_KEY",
        "hf": "HUGGINGFACE_API_KEY",
    }.get(provider)
    if not key_name:
        return False
    key = os.getenv(key_name, "").strip()
    return bool(key) and "dummy" not in key


def demo_candidate(chunk: SourceChunk, competency_id: str, target_level: str) -> dict:
    name = KNOWN_COMPETENCIES[competency_id][0]
    correct = chunk.text
    return {
        "question": f"Which statement is supported by the section {chunk.section}?",
        "options": [
            correct,
            "Every dwelling is automatically included even when it is missing from the frame.",
            "Allocation notes should omit the stratum name.",
            "A chart colour is a sampling unit.",
        ],
        "correct_option": correct,
        "explanation": f"The source section {chunk.section} states: {chunk.text}",
        "source_chunk_ids": [chunk.id],
        "competency_id": competency_id,
        "target_level": target_level,
        "origin": "demo_draft",
        "competency_name": name,
    }


def call_model(prompt: str) -> str:
    """Server-side model call. Tests replace this. Failure stores no draft."""
    if not model_available():
        raise GenerationError(UNAVAILABLE, 503)
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    if provider == "groq":
        url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/") + "/chat/completions"
        key = os.getenv("GROQ_API_KEY", "")
        model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    elif provider == "openrouter":
        url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/") + "/chat/completions"
        key = os.getenv("OPENROUTER_API_KEY", "")
        model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
    else:
        url = os.getenv("HUGGINGFACE_BASE_URL", "https://router.huggingface.co/v1").rstrip("/") + "/chat/completions"
        key = os.getenv("HUGGINGFACE_API_KEY", "")
        model = os.getenv("HUGGINGFACE_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
    payload = json.dumps(
        {
            "model": model,
            "temperature": 0.2,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode()
    request = __import__("urllib.request", fromlist=["Request"]).Request(
        url,
        data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with __import__("urllib.request", fromlist=["urlopen"]).urlopen(request, timeout=20) as response:
            body = json.loads(response.read().decode())
        return str(body["choices"][0]["message"]["content"])
    except Exception as exc:
        raise GenerationError(UNAVAILABLE, 503) from exc


def candidates_from_model(
    raw_payloads: list[str],
    chunks: list[SourceChunk],
    competency_id: str,
    target_level: str,
) -> list[dict]:
    allowed = {chunk.id for chunk in chunks}
    name = KNOWN_COMPETENCIES[competency_id][0]
    validated = []
    for raw in raw_payloads:
        parsed = parse_model_json(raw)
        item = validate_candidate(parsed, allowed, competency_id, target_level)
        item["origin"] = "model"
        item["competency_name"] = name
        validated.append(item)
    return validated
