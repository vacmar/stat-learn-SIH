import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.auth import get_current_learner
from app.models.domain import Learner
from app.repository import state_repo

router = APIRouter(prefix="/goals", tags=["Goals"])


class GoalCreateRequest(BaseModel):
    title: str
    target_role_id: str | None = None
    active: bool = True


@router.post("/")
def create_goal(
    req: GoalCreateRequest, learner: Learner = Depends(get_current_learner)
):
    goal_id = uuid.uuid4().hex
    now = datetime.now(UTC).isoformat()
    goal = {
        "goal_id": goal_id,
        "learner_id": learner.learner_id,
        "title": req.title,
        "target_role_id": req.target_role_id or learner.target_role_id,
        "active": req.active,
        "progress": 0,
        "created_at": now,
    }
    if req.active:
        for g in state_repo.get_goals_for_learner(learner.learner_id):
            if g.get("active"):
                g["active"] = False
                state_repo.save_goal(g)
    state_repo.save_goal(goal)
    return goal


@router.get("/")
def get_goals(learner: Learner = Depends(get_current_learner)):
    goals = state_repo.get_goals_for_learner(learner.learner_id)
    if goals:
        return goals
    return [
        {"title": "Data Engineering Master", "active": True, "progress": 45},
        {"title": "AI / Machine Learning Specialist", "active": False, "progress": 0},
    ]


@router.get("/{goal_id}")
def get_goal(goal_id: str, learner: Learner = Depends(get_current_learner)):
    goal = state_repo.get_goal(goal_id)
    if not goal or goal.get("learner_id") != learner.learner_id:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal
