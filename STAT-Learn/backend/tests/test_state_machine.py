from app.models.domain import NodeStatus, PathNode
from app.models.payloads import CompletionRequest
from app.repository import state_repo
from app.services import progression_service


def setup_function():
    state_repo.db["nodes"].clear()
    state_repo.db["prerequisites"].clear()


def test_node_completion_unlocks_next():
    # Setup mock state
    node1 = PathNode(
        node_id="n1",
        path_id="p1",
        course_id="c1",
        sequence_order=1,
        status=NodeStatus.IN_PROGRESS,
    )
    node2 = PathNode(
        node_id="n2",
        path_id="p1",
        course_id="c2",
        sequence_order=2,
        status=NodeStatus.LOCKED,
    )

    state_repo.update_node(node1)
    state_repo.update_node(node2)
    state_repo.db["course_skills"]["c1"] = ["skill_a"]
    state_repo.db["prerequisites"]["c2"] = [
        {"skill_id": "skill_a", "required_proficiency": 0.8}
    ]

    # Attempt completion (pass)
    req = CompletionRequest(learner_id="L1", assessment_score=85.0, practical_pass=True)
    res = progression_service.attempt_completion("L1", "n1", req)

    assert res["status"] == "COMPLETED"
    assert state_repo.get_node("n1").status == NodeStatus.COMPLETED
    assert state_repo.get_node("n2").status == NodeStatus.UNLOCKED


def test_node_completion_fails_threshold():
    node1 = PathNode(
        node_id="n1",
        path_id="p1",
        course_id="c1",
        sequence_order=1,
        status=NodeStatus.IN_PROGRESS,
    )
    state_repo.update_node(node1)

    # Attempt completion (fail score)
    req = CompletionRequest(learner_id="L1", assessment_score=75.0, practical_pass=True)
    res = progression_service.attempt_completion("L1", "n1", req)

    assert res["status"] == "REMEDIATION"
    assert state_repo.get_node("n1").status == NodeStatus.REMEDIATION
