from datetime import UTC, datetime

from app.models.domain import NodeStatus
from app.models.payloads import CompletionRequest
from app.repository import state_repo
from app.services import unlock_service
from app.services.cache_service import invalidate_node_cache


def build_resume_payload(learner_id: str, node_id: str) -> dict:
    """Resume helper: module, concept, progress, weak concepts, next action."""
    node = state_repo.get_node(node_id)
    if not node:
        raise ValueError("Node not found")

    progress = state_repo.get_learning_progress(learner_id, node_id) or {}
    context = state_repo.get_node_context(node_id) or {}
    concepts = context.get("concepts") or progress.get("concepts") or []

    mistakes = state_repo.get_mistakes(learner_id, node_id)
    weak_map: dict[str, dict] = {}
    for m in mistakes:
        c = m["concept"]
        if c not in weak_map:
            weak_map[c] = {"concept": c, "error_count": 0}
        weak_map[c]["error_count"] += 1

    current_concept = progress.get("current_concept")
    if not current_concept and concepts:
        current_concept = concepts[0]

    percent = float(progress.get("percent_complete", 0.0))
    next_action = progress.get("next_action")
    if not next_action:
        if node.status == NodeStatus.IN_PROGRESS:
            next_action = "continue_lesson"
        elif node.status == NodeStatus.UNLOCKED:
            next_action = "start_node"
        elif node.status == NodeStatus.COMPLETED:
            next_action = "review"
        else:
            next_action = "unlock_prerequisites"

    return {
        "node_id": node_id,
        "module": progress.get("current_module", "lesson"),
        "concept": current_concept,
        "progress_percent": percent,
        "weak_concepts": list(weak_map.values()),
        "next_action": next_action,
        "status": node.status.value,
    }


def attempt_completion(learner_id: str, node_id: str, req: CompletionRequest) -> dict:
    node = state_repo.get_node(node_id)
    if not node:
        raise ValueError("Node not found")

    # Idempotency check
    if node.status == NodeStatus.COMPLETED:
        unlocked = unlock_service.check_unlocks(learner_id, node.path_id)
        next_node = unlock_service.get_next_recommended_node(learner_id, node.path_id)
        return {
            "node_id": node_id,
            "status": "COMPLETED",
            "skills_updated": [],
            "unlocked_nodes": unlocked,
            "next_recommended_node": next_node,
        }

    skills_updated = []

    # Rules: Assessment >= 80% and practical pass
    if req.assessment_score >= 80.0 and req.practical_pass:
        # 1. Update Node Status
        node.status = NodeStatus.COMPLETED
        state_repo.update_node(node)

        # 2. Record Evidence & Recalculate Proficiency
        # In a real system with SQL, this block would be wrapped in a DB transaction
        skills = state_repo.get_course_skills(node.course_id)
        timestamp = datetime.now(UTC).isoformat()

        for skill_id in skills:
            # Get existing proficiency
            old_prof_obj = state_repo.get_learner_proficiency(learner_id, skill_id)
            old_prof = old_prof_obj["proficiency"]

            # Record new evidence
            new_evidence_score = (
                req.assessment_score / 100.0
                if req.assessment_score > 1.0
                else req.assessment_score
            )
            state_repo.record_skill_evidence(
                learner_id=learner_id,
                skill_id=skill_id,
                source_type="COURSE_COMPLETION",
                source_id=node_id,
                score=new_evidence_score,
                confidence=0.8,
                timestamp=timestamp,
            )

            # Simplified mock fusion: just take the max for MVP
            new_prof = max(old_prof, new_evidence_score)

            state_repo.update_learner_proficiency(
                learner_id=learner_id,
                skill_id=skill_id,
                proficiency=new_prof,
                confidence=0.8,
            )

            skills_updated.append(
                {
                    "skill_id": skill_id,
                    "previous_proficiency": old_prof,
                    "new_proficiency": new_prof,
                }
            )

        # 3. Check downstream unlocks based on new skill proficiencies
        unlocked_nodes = unlock_service.check_unlocks(learner_id, node.path_id)

        # 4. Recommend Next Node
        next_node = unlock_service.get_next_recommended_node(learner_id, node.path_id)

        # Trigger cache invalidate (After DB commit)
        invalidate_node_cache(
            node_id=node_id,
            conversation_id=f"conv_{node_id}",
            assessment_id=f"assess_{node_id}",
        )

        return {
            "node_id": node_id,
            "status": "COMPLETED",
            "skills_updated": skills_updated,
            "unlocked_nodes": unlocked_nodes,
            "next_recommended_node": next_node,
        }

    node.status = NodeStatus.REMEDIATION
    state_repo.update_node(node)

    return {
        "node_id": node_id,
        "status": "REMEDIATION",
        "skills_updated": [],
        "unlocked_nodes": [],
        "next_recommended_node": None,
    }
