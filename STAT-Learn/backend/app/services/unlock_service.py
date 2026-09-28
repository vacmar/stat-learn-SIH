from app.models.domain import NodeStatus, PathNode
from app.repository import state_repo


def _humanize_id(raw: str) -> str:
    """Turn ai_python_basics / skill_a into a readable label."""
    s = (raw or "").strip()
    for prefix in ("skill_", "c_", "ai_"):
        if s.lower().startswith(prefix):
            s = s[len(prefix) :]
            break
    parts = [p for p in s.replace("-", "_").split("_") if p]
    return " ".join(p.capitalize() for p in parts) if parts else raw


def _course_title(course_id: str) -> str:
    course = state_repo.db.get("courses", {}).get(course_id, {})
    title = (course or {}).get("title")
    if title:
        return str(title)
    return _humanize_id(course_id)


def _evaluate_prereqs(learner_id: str, course_id: str) -> list:
    """Returns a list of structured lock reasons if prerequisites are unmet."""
    prereqs = state_repo.get_prerequisites(course_id)
    reasons = []

    for req in prereqs:
        skill_id = req["skill_id"]
        required = req["required_proficiency"]

        prof = state_repo.get_learner_proficiency(learner_id, skill_id)
        current = prof["proficiency"]

        if current < required:
            title = _humanize_id(skill_id)
            reasons.append(
                {
                    "prerequisite_skill": skill_id,
                    "prerequisite_title": title,
                    "required_proficiency": required,
                    "current_proficiency": current,
                    "status": "INSUFFICIENT_MASTERY",
                    "message": (
                        f"Needs more mastery in {title} "
                        f"({round(current * 100)}% / {round(required * 100)}%)"
                    ),
                }
            )

    return reasons


def check_unlocks(learner_id: str, path_id: str) -> list[str]:
    """Unlock the next path node only after prior nodes in sequence are COMPLETED."""
    nodes = [n for n in state_repo.db["nodes"].values() if n.path_id == path_id]
    nodes.sort(key=lambda n: n.sequence_order)

    unlocked_nodes: list[str] = []
    for index, node in enumerate(nodes):
        if node.status != NodeStatus.LOCKED:
            continue
        # Sequence gate: every earlier node must be completed
        prior = nodes[:index]
        if prior and not all(p.status == NodeStatus.COMPLETED for p in prior):
            continue
        # Also respect skill prerequisites when defined
        reasons = _evaluate_prereqs(learner_id, node.course_id)
        if reasons:
            continue
        node.status = NodeStatus.UNLOCKED
        state_repo.update_node(node)
        unlocked_nodes.append(node.node_id)
    return unlocked_nodes


def _immediate_previous(node: PathNode) -> PathNode | None:
    path_nodes = state_repo.get_nodes_for_path(node.path_id)
    path_nodes.sort(key=lambda n: n.sequence_order)
    previous = None
    for prior in path_nodes:
        if prior.sequence_order >= node.sequence_order:
            break
        previous = prior
    return previous


def get_lock_explanation(learner_id: str, node_id: str) -> dict:
    """Returns structured reasons for why a node is locked.

    Sequential paths only cite the immediate previous node (no cascading list
    of every ancestor). Skill thresholds are shown only after that gate is met.
    """
    node = state_repo.get_node(node_id)
    if not node:
        return {"locked": False, "reasons": []}

    previous = _immediate_previous(node)
    if previous and previous.status != NodeStatus.COMPLETED:
        title = _course_title(previous.course_id)
        reasons = [
            {
                "prerequisite_skill": previous.course_id,
                "prerequisite_title": title,
                "required_proficiency": 1.0,
                "current_proficiency": 0.0,
                "status": "PRIOR_NODE_INCOMPLETE",
                "message": f"Complete “{title}” first",
            }
        ]
        return {"locked": True, "reasons": reasons}

    reasons = _evaluate_prereqs(learner_id, node.course_id)
    locked = len(reasons) > 0 or node.status == NodeStatus.LOCKED
    return {"locked": locked, "reasons": reasons}


def get_next_recommended_node(learner_id: str, path_id: str) -> str | None:
    """Ranks eligible nodes using a dependency-aware scoring formula and skips completed nodes."""
    eligible_nodes = []

    for node_id, node in state_repo.db["nodes"].items():
        if node.path_id == path_id and node.status in [
            NodeStatus.UNLOCKED,
            NodeStatus.IN_PROGRESS,
        ]:
            eligible_nodes.append(node)

    if not eligible_nodes:
        return None

    # Dependency-aware scoring (mocked simple logic for MVP)
    # Higher sequence_order but prioritizing IN_PROGRESS over UNLOCKED
    best_node = None
    best_score: float = -1.0

    for node in eligible_nodes:
        score: float = 0.0

        # 0.35 * skill_gap_reduction (mock 1.0 for simplicity)
        score += 0.35 * 1.0

        # 0.15 * prerequisite_validity (if IN_PROGRESS, it's very valid to continue)
        if node.status == NodeStatus.IN_PROGRESS:
            score += 0.50

        # Tie-breaker: sequence order (prefer earlier nodes)
        score -= node.sequence_order * 0.01

        if score > best_score:
            best_score = score
            best_node = node.node_id

    return best_node
