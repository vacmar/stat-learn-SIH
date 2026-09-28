from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.auth import get_current_learner
from app.models.domain import Learner
from app.repository import state_repo

router = APIRouter(prefix="/learners", tags=["Learners"])


class LearnerPatch(BaseModel):
    name: str | None = None
    target_role_id: str | None = None
    target_domain: str | None = None
    goals: list[str] | None = None
    experience_level: str | None = None
    prior_experience: str | None = None
    education: str | None = None
    known_skills: list[str] | None = None
    interests: list[str] | None = None
    learning_style: str | None = None
    weekly_time: int | None = None


class LearnerSkillsPayload(BaseModel):
    skills: list[str]
    self_reported_proficiency: dict[str, float] = Field(default_factory=dict)


class LearnerEvidencePayload(BaseModel):
    skill_id: str
    source_type: str
    source_id: str
    score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0, default=0.7)


@router.get("/me")
def get_me(learner: Learner = Depends(get_current_learner)):
    return learner


@router.patch("/me")
def patch_me(req: LearnerPatch, learner: Learner = Depends(get_current_learner)):
    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(learner, key, value)

    state_repo.update_learner(learner)
    return {"message": "Profile updated successfully"}


@router.post("/{learner_id}/skills")
def add_learner_skills(learner_id: str, payload: LearnerSkillsPayload):
    learner = state_repo.get_learner(learner_id)
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    merged = list(set(learner.known_skills + payload.skills))
    learner.known_skills = merged
    if payload.self_reported_proficiency:
        learner.self_reported_proficiency.update(payload.self_reported_proficiency)
    learner.updated_at = datetime.now(UTC).isoformat()
    state_repo.update_learner(learner)

    return {
        "learner_id": learner_id,
        "known_skills": learner.known_skills,
        "self_reported_proficiency": learner.self_reported_proficiency,
    }


@router.post("/{learner_id}/evidence")
def add_learner_evidence(learner_id: str, payload: LearnerEvidencePayload):
    learner = state_repo.get_learner(learner_id)
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    ts = datetime.now(UTC).isoformat()
    state_repo.record_skill_evidence(
        learner_id=learner_id,
        skill_id=payload.skill_id,
        source_type=payload.source_type,
        source_id=payload.source_id,
        score=payload.score,
        confidence=payload.confidence,
        timestamp=ts,
    )
    old = state_repo.get_learner_proficiency(learner_id, payload.skill_id)
    new_prof = max(old["proficiency"], payload.score)
    state_repo.update_learner_proficiency(
        learner_id, payload.skill_id, new_prof, payload.confidence
    )
    return {
        "learner_id": learner_id,
        "skill_id": payload.skill_id,
        "proficiency": new_prof,
        "confidence": payload.confidence,
    }
