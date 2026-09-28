"""HTTP client for the manthaino AI service."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from app.models.domain import Learner

logger = logging.getLogger(__name__)


def _ai_base_url() -> str:
    return os.getenv("AI_SERVICE_URL", "http://localhost:8001").rstrip("/")


def build_path_generate_payload(
    learner: Learner,
    *,
    role_title: str | None = None,
    path_role_id: str | None = None,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    profile = profile or {}
    title = (
        role_title
        or profile.get("role_title")
        or profile.get("custom_role_title")
        or learner.target_role_id
        or "Learner"
    )
    # Prefer clean domain without the "Custom role:" prefix we store for UI
    domain = learner.target_domain or ""
    if domain.startswith("Custom role:"):
        parts = [p.strip() for p in domain.split("|")]
        domain = (
            " | ".join(
                p for p in parts if not p.lower().startswith("custom role:")
            ).strip()
            or None
        )

    return {
        "learner_id": learner.learner_id,
        "name": learner.name,
        "target_role": title,
        "target_role_id": path_role_id
        or profile.get("target_role")
        or learner.target_role_id,
        "custom_role_title": profile.get("custom_role_title")
        or (title if learner.target_role_id == "role_other" else None),
        "target_domain": domain or learner.target_domain,
        "experience_level": learner.experience_level,
        "prior_experience": learner.prior_experience,
        "known_skills": learner.known_skills or [],
        "interests": learner.interests or [],
        "learning_style": learner.learning_style,
        "weekly_time": learner.weekly_time or 10,
        "goals": learner.goals or [],
    }


def request_ai_pathway(
    payload: dict[str, Any], timeout: float = 45.0
) -> dict[str, Any]:
    """POST /path/generate and return the PathwayExplanation JSON."""
    url = f"{_ai_base_url()}/path/generate"
    with httpx.Client(timeout=timeout) as client:
        res = client.post(url, json=payload)
        res.raise_for_status()
        return res.json()
