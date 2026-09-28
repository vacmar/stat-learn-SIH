from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.domain import NodeStatus
from app.models.payloads import CompletionRequest
from app.repository import state_repo
from app.services import progression_service

router = APIRouter(prefix="/nodes", tags=["Nodes"])


class MistakePayload(BaseModel):
    learner_id: str
    concept: str
    description: str


class StartNodePayload(BaseModel):
    learner_id: str
    current_module: str = "lesson"
    current_concept: str | None = None


@router.get("/{node_id}")
def get_node(node_id: str):
    node = state_repo.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"node_id": node_id, "node": node.model_dump()}


@router.get("/{node_id}/context")
def get_node_context(node_id: str):
    """Returns structured pedagogical context."""
    context = state_repo.get_node_context(node_id)
    if not context:
        raise HTTPException(status_code=404, detail="Node context not found")
    return context


@router.post("/{node_id}/mistakes")
def record_mistake(node_id: str, payload: MistakePayload):
    """Records a learner mistake durably."""
    timestamp = datetime.now(UTC).isoformat()
    state_repo.record_mistake(
        learner_id=payload.learner_id,
        node_id=node_id,
        concept=payload.concept,
        description=payload.description,
        timestamp=timestamp,
    )
    return {"status": "success", "recorded_at": timestamp}


@router.get("/{node_id}/mistakes")
def get_weak_concepts(node_id: str, learner_id: str):
    """Aggregates mistakes into weak concepts."""
    mistakes = state_repo.get_mistakes(learner_id, node_id)

    aggregation = {}
    for m in mistakes:
        c = m["concept"]
        if c not in aggregation:
            aggregation[c] = {"concept": c, "error_count": 0, "latest_description": ""}
        aggregation[c]["error_count"] += 1
        aggregation[c]["latest_description"] = m["description"]

    return {"weak_concepts": list(aggregation.values())}


@router.post("/{node_id}/start")
def start_node(node_id: str, payload: StartNodePayload):
    node = state_repo.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    if node.status in (NodeStatus.LOCKED, NodeStatus.COMPLETED):
        raise HTTPException(
            status_code=400,
            detail=f"Node cannot be started from status {node.status.value}",
        )

    started_at = datetime.now(UTC).isoformat()
    node.status = NodeStatus.IN_PROGRESS
    state_repo.update_node(node)

    context = state_repo.get_node_context(node_id) or {}
    concepts = context.get("concepts") or []
    progress = {
        "learner_id": payload.learner_id,
        "node_id": node_id,
        "status": NodeStatus.IN_PROGRESS.value,
        "started_at": started_at,
        "current_module": payload.current_module,
        "current_concept": payload.current_concept
        or (concepts[0] if concepts else None),
        "percent_complete": 0.0,
        "next_action": "continue_lesson",
        "concepts": concepts,
    }
    state_repo.save_learning_progress(payload.learner_id, node_id, progress)

    return {"node_id": node_id, "status": node.status.value, "progress": progress}


@router.get("/{node_id}/progress")
def get_node_progress(node_id: str, learner_id: str):
    node = state_repo.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    progress = state_repo.get_learning_progress(learner_id, node_id)
    if not progress:
        return {
            "node_id": node_id,
            "learner_id": learner_id,
            "status": node.status.value,
            "progress": None,
        }
    return {"node_id": node_id, "learner_id": learner_id, "progress": progress}


@router.get("/{node_id}/resume")
def resume_node(node_id: str, learner_id: str):
    try:
        payload = progression_service.build_resume_payload(learner_id, node_id)
        return payload
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{node_id}/unlock-conditions")
def get_unlock_conditions(node_id: str, learner_id: str):
    from app.services import unlock_service

    return unlock_service.get_lock_explanation(learner_id, node_id)


@router.post("/{node_id}/complete")
def complete_node(node_id: str, req: CompletionRequest):
    try:
        result = progression_service.attempt_completion(req.learner_id, node_id, req)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
