from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.auth import get_current_learner
from app.models.domain import Learner
from app.repository import state_repo

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])

ROLE_CATALOG = [
    {
        "id": "role_de",
        "title": "Data Engineer",
        "description": "Master scalable pipelines and warehouses.",
        "icon": "Database",
    },
    {
        "id": "role_be",
        "title": "Backend Developer",
        "description": "Create robust APIs and services.",
        "icon": "TerminalSquare",
    },
    {
        "id": "role_fe",
        "title": "Frontend Developer",
        "description": "Build polished web interfaces.",
        "icon": "Layout",
    },
    {
        "id": "role_ai",
        "title": "AI Engineer",
        "description": "Build intelligent systems and LLM apps.",
        "icon": "BrainCircuit",
    },
    {
        "id": "role_mlops",
        "title": "MLOps Engineer",
        "description": "Ship and monitor ML in production.",
        "icon": "Cog",
    },
    {
        "id": "role_other",
        "title": "Other",
        "description": "Describe a role that is not listed.",
        "icon": "MoreHorizontal",
    },
]

ROLE_TITLES = {r["id"]: r["title"] for r in ROLE_CATALOG}

LEARNING_STYLES = [
    {"id": "visual", "label": "Visual", "description": "Diagrams, demos, and examples"},
    {
        "id": "hands_on",
        "label": "Hands-on",
        "description": "Learn by building and breaking things",
    },
    {
        "id": "reading",
        "label": "Reading",
        "description": "Docs, articles, and written notes",
    },
    {"id": "mixed", "label": "Mixed", "description": "A blend of the above"},
]

WEEKLY_TIME_OPTIONS = [5, 10, 15, 20]


class OnboardingRequest(BaseModel):
    name: str | None = None
    target_role_id: str
    custom_role_title: str | None = None
    target_domain: str | None = None
    goals: list[str] = []
    experience_level: str
    prior_experience: str | None = None
    known_skills: list[str] = []
    self_reported_proficiency: dict[str, float] = {}
    interests: list[str] = []
    learning_style: str | None = None
    weekly_time: int | None = Field(default=10, ge=1, le=168)


def resolve_role_title(role_id: str | None, custom_title: str | None = None) -> str:
    if role_id == "role_other" and custom_title:
        return custom_title.strip()
    if role_id and role_id in ROLE_TITLES:
        return ROLE_TITLES[role_id]
    return role_id or "Unknown role"


@router.get("/")
def get_onboarding_options():
    return {
        "roles": ROLE_CATALOG,
        "experience_levels": ["Beginner", "Intermediate", "Expert"],
        "learning_styles": LEARNING_STYLES,
        "weekly_time_options": WEEKLY_TIME_OPTIONS,
        "role_titles": ROLE_TITLES,
    }


@router.post("/")
def save_onboarding(
    req: OnboardingRequest, learner: Learner = Depends(get_current_learner)
):
    if req.target_role_id not in ROLE_TITLES:
        raise HTTPException(status_code=422, detail="Invalid target role")
    if req.target_role_id == "role_other" and not (req.custom_role_title or "").strip():
        raise HTTPException(
            status_code=422, detail="Please describe your target role for Other"
        )
    if req.learning_style and req.learning_style not in {
        s["id"] for s in LEARNING_STYLES
    }:
        raise HTTPException(status_code=422, detail="Invalid learning style")

    custom_title = (req.custom_role_title or "").strip() or None
    role_title = resolve_role_title(req.target_role_id, custom_title)

    # Keep catalog id for analytics; AI path generation uses the human role title
    # and full onboarding answers — do not force unknown Other roles onto Data Eng.
    path_role_id = req.target_role_id
    if path_role_id not in state_repo.db.get("target_roles", {}):
        path_role_id = (
            "role_other"
            if "role_other" in state_repo.db.get("target_roles", {})
            else "role_de"
        )

    if req.name and req.name.strip():
        learner.name = req.name.strip()

    learner.target_role_id = req.target_role_id
    # Persist human title + optional domain for UI (domain keeps free-text context)
    domain_parts = []
    if custom_title and req.target_role_id == "role_other":
        domain_parts.append(f"Custom role: {custom_title}")
    if req.target_domain:
        domain_parts.append(req.target_domain.strip())
    learner.target_domain = (
        " | ".join(domain_parts) if domain_parts else req.target_domain
    )
    learner.goals = req.goals or [f"Become a {role_title}"]
    learner.experience_level = req.experience_level
    learner.prior_experience = req.prior_experience
    learner.known_skills = [s.strip() for s in req.known_skills if s and s.strip()]
    learner.self_reported_proficiency = req.self_reported_proficiency
    learner.interests = [s.strip() for s in req.interests if s and s.strip()]
    learner.learning_style = req.learning_style
    learner.weekly_time = req.weekly_time

    learner.onboarding_completed = True
    learner.onboarding_version = 2
    learner.onboarding_completed_at = datetime.now(UTC).isoformat()
    learner.updated_at = learner.onboarding_completed_at

    state_repo.update_learner(learner)

    try:
        from app.services import replanning_service

        state_repo.db.setdefault("learner_profiles", {})[learner.learner_id] = {
            "target_role": path_role_id,
            "role_title": role_title,
            "custom_role_title": custom_title,
            "onboarding_answers": {
                "name": learner.name,
                "target_role": role_title,
                "domain": (req.target_domain or "").strip() or None,
                "experience_level": req.experience_level,
                "prior_experience": req.prior_experience,
                "known_skills": learner.known_skills,
                "interests": learner.interests,
                "learning_style": req.learning_style,
                "weekly_time": req.weekly_time,
                "goals": learner.goals,
            },
        }
        # Always (re)build path from AI using the full onboarding profile.
        existing = state_repo.get_active_path(learner.learner_id)
        if existing:
            existing.is_active = False
            state_repo.save_path(existing)
        replanning_service.generate_path_for_learner(learner.learner_id, path_role_id)
    except Exception as e:
        print(f"Failed to generate path: {e}")

    return {
        "message": "Onboarding completed successfully",
        "role_title": role_title,
        "path_role_id": path_role_id,
    }
