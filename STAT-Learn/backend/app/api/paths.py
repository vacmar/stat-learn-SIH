from fastapi import APIRouter, Depends, HTTPException

from app.api.auth import get_current_learner
from app.models.domain import Learner
from app.repository import state_repo

router = APIRouter(prefix="/paths", tags=["Paths"])


@router.post("/generate")
def generate_path(learner: Learner = Depends(get_current_learner)):
    from app.services import replanning_service

    profiles = state_repo.db.setdefault("learner_profiles", {})
    profile = profiles.get(learner.learner_id) or {}
    if learner.target_role_id:
        profile["target_role"] = profile.get("target_role") or learner.target_role_id
        if learner.goals:
            profile.setdefault("role_title", learner.goals[0].replace("Become a ", ""))
        profiles[learner.learner_id] = profile
    try:
        # Force a fresh AI path when none is active (e.g. after backend restart)
        existing = state_repo.get_active_path(learner.learner_id)
        if existing:
            existing.is_active = False
            state_repo.save_path(existing)
        result = replanning_service.generate_path_for_learner(
            learner.learner_id,
            profile.get("target_role") or learner.target_role_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/me/ensure")
def ensure_active_path(learner: Learner = Depends(get_current_learner)):
    """Return the active path, regenerating via AI if memory was wiped (restart)."""
    from app.services import replanning_service

    regenerated = False
    path = state_repo.get_active_path(learner.learner_id)
    if not path:
        if not learner.onboarding_completed and not learner.target_role_id:
            raise HTTPException(
                status_code=404,
                detail="No active path found. Complete onboarding first.",
            )
        profiles = state_repo.db.setdefault("learner_profiles", {})
        profile = profiles.get(learner.learner_id) or {}
        profile["target_role"] = profile.get("target_role") or learner.target_role_id
        if learner.goals and not profile.get("role_title"):
            profile["role_title"] = learner.goals[0].replace("Become a ", "")
        profiles[learner.learner_id] = profile
        try:
            replanning_service.generate_path_for_learner(
                learner.learner_id,
                profile.get("target_role") or learner.target_role_id,
            )
            regenerated = True
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        path = state_repo.get_active_path(learner.learner_id)
        if not path:
            raise HTTPException(status_code=500, detail="Path regeneration failed")

    nodes = state_repo.get_nodes_for_path(path.path_id)
    enriched = []
    for n in nodes:
        course = state_repo.db.get("courses", {}).get(n.course_id, {})
        payload = n.model_dump()
        payload["course_title"] = course.get("title", n.course_id)
        enriched.append(payload)
    return {
        "path_id": path.path_id,
        "nodes": enriched,
        "is_active": True,
        "goal": learner.goals[0] if learner.goals else "Personalized Pathway",
        "regenerated": regenerated,
    }


@router.get("/me/active")
def get_me_active_path(learner=Depends(get_current_learner)):
    learner_id = learner.learner_id
    path = state_repo.get_active_path(learner_id)
    if not path:
        raise HTTPException(
            status_code=404,
            detail="No active path found. Complete onboarding first.",
        )

    nodes = state_repo.get_nodes_for_path(path.path_id)
    enriched = []
    for n in nodes:
        course = state_repo.db.get("courses", {}).get(n.course_id, {})
        payload = n.model_dump()
        payload["course_title"] = course.get("title", n.course_id)
        enriched.append(payload)
    return {
        "path_id": path.path_id,
        "nodes": enriched,
        "is_active": True,
        "goal": learner.goals[0] if learner.goals else "Personalized Pathway",
    }


@router.get("/{path_id}")
def get_path(path_id: str):
    path = state_repo.get_path(path_id)
    if not path:
        raise HTTPException(status_code=404, detail="Path not found")
    nodes = state_repo.get_nodes_for_path(path_id)
    return {
        "path_id": path.path_id,
        "learner_id": path.learner_id,
        "version": path.version,
        "is_active": path.is_active,
        "nodes": [n.model_dump() for n in nodes],
    }


from pydantic import BaseModel


class RegenerateRequest(BaseModel):
    learner_id: str


@router.post("/{path_id}/regenerate")
def regenerate_path(path_id: str, req: RegenerateRequest):
    from app.services import replanning_service

    try:
        res = replanning_service.regenerate_path(req.learner_id, path_id)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{path_id}/next-node")
def get_next_node(path_id: str, learner_id: str):
    from app.services import unlock_service

    next_node = unlock_service.get_next_recommended_node(learner_id, path_id)
    if not next_node:
        raise HTTPException(status_code=404, detail="No eligible next node found")
    return {"next_recommended_node": next_node}
