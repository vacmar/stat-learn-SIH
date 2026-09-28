from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.auth import get_current_learner
from app.repository import state_repo
from app.services import project_service

router = APIRouter(prefix="/projects", tags=["Projects"])


class ProjectSubmission(BaseModel):
    learner_id: str
    artifact: str


class RequirementEvaluation(BaseModel):
    requirement_id: str
    status: str
    evidence: str


class SkillDemonstration(BaseModel):
    skill_id: str
    score: float
    confidence: float


class ProjectEvaluation(BaseModel):
    submission_id: str
    score: float
    passed: bool
    requirements: list[RequirementEvaluation]
    skills_demonstrated: list[SkillDemonstration]
    strengths: list[str]
    improvements: list[str]


@router.get("/me/recommended")
def get_recommended_project(learner=Depends(get_current_learner)):
    profile = state_repo.db.get("learner_profiles", {}).get(learner.learner_id, {})
    projects = state_repo.db.get("projects", {})

    # Prefer AI-authored capstone for this learner
    recommended_id = profile.get("recommended_project_id")
    if recommended_id and recommended_id in projects:
        return {"project_id": recommended_id, "project": projects[recommended_id]}

    for project_id, project in projects.items():
        if project.get("learner_id") == learner.learner_id:
            return {"project_id": project_id, "project": project}

    role = learner.target_role_id or "role_be"
    path_role = profile.get("target_role", role)
    for project_id, project in projects.items():
        roles = project.get("roles") or []
        if path_role in roles or role in roles:
            return {"project_id": project_id, "project": project}
    # fallback
    first_id = next(iter(projects), "proj_1")
    return {"project_id": first_id, "project": projects.get(first_id, {})}


@router.get("/{project_id}")
def get_project(project_id: str):
    project = state_repo.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"project_id": project_id, "project": project}


@router.post("/{project_id}/submit")
def submit_project(project_id: str, req: ProjectSubmission):
    try:
        res = project_service.submit_project(req.learner_id, project_id, req.artifact)
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{project_id}/evaluate")
def evaluate_project(project_id: str, req: ProjectEvaluation):
    try:
        # Pass the full structured req dictionary to the service
        res = project_service.evaluate_project(project_id, req.model_dump())
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
