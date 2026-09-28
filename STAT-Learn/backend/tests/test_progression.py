import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.domain import NodeStatus, PathNode
from app.repository import state_repo

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    state_repo.db["nodes"].clear()
    state_repo.db["prerequisites"].clear()
    state_repo.db["evidence"].clear()
    state_repo.db["proficiency"].clear()
    state_repo.db["course_skills"].clear()

    # Setup base state
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
    node3 = PathNode(
        node_id="n3",
        path_id="p1",
        course_id="c3",
        sequence_order=3,
        status=NodeStatus.LOCKED,
    )

    state_repo.update_node(node1)
    state_repo.update_node(node2)
    state_repo.update_node(node3)

    state_repo.db["course_skills"]["c1"] = ["skill_a", "skill_b"]
    state_repo.db["course_skills"]["c2"] = ["skill_c"]

    state_repo.db["prerequisites"]["c2"] = [
        {"skill_id": "skill_a", "required_proficiency": 0.8}
    ]
    state_repo.db["prerequisites"]["c3"] = [
        {"skill_id": "skill_c", "required_proficiency": 0.5}
    ]


def test_successful_completion_updates_evidence():
    req = {"learner_id": "L1", "assessment_score": 85.0, "practical_pass": True}
    res = client.post("/nodes/n1/complete", json=req)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "COMPLETED"

    # Multiple skills taught by one node update correctly
    assert len(data["skills_updated"]) == 2

    # Evidence provenance is preserved
    evidence = state_repo.get_skill_evidence("L1", "skill_a")
    assert len(evidence) == 1
    assert evidence[0]["source_type"] == "COURSE_COMPLETION"
    assert evidence[0]["score"] == 0.85


def test_failed_completion_does_not_update_evidence():
    req = {"learner_id": "L1", "assessment_score": 75.0, "practical_pass": True}
    res = client.post("/nodes/n1/complete", json=req)
    assert res.status_code == 200
    assert res.json()["status"] == "REMEDIATION"
    assert len(res.json()["skills_updated"]) == 0
    assert len(state_repo.get_skill_evidence("L1", "skill_a")) == 0


def test_lock_explanation_reports_missing_prerequisite():
    # Sequence gate: previous node must be completed before skill prereqs matter
    res = client.get("/nodes/n2/unlock-conditions?learner_id=L1")
    assert res.status_code == 200
    data = res.json()
    assert data["locked"] is True
    assert len(data["reasons"]) == 1
    assert data["reasons"][0]["status"] == "PRIOR_NODE_INCOMPLETE"
    assert "Complete" in data["reasons"][0]["message"]

    # After previous node is complete, skill threshold is the remaining lock reason
    n1 = state_repo.get_node("n1")
    n1.status = NodeStatus.COMPLETED
    state_repo.update_node(n1)
    n2 = state_repo.get_node("n2")
    n2.status = NodeStatus.LOCKED
    state_repo.update_node(n2)
    state_repo.update_learner_proficiency("L1", "skill_a", 0.0, 0.0)

    res2 = client.get("/nodes/n2/unlock-conditions?learner_id=L1")
    data2 = res2.json()
    assert data2["locked"] is True
    assert data2["reasons"][0]["prerequisite_skill"] == "skill_a"
    assert data2["reasons"][0]["required_proficiency"] == 0.8
    assert "message" in data2["reasons"][0]


def test_lock_explanation_only_cites_immediate_previous_node():
    """Locked later tiers must not list every ancestor — only the previous node."""
    res = client.get("/nodes/n3/unlock-conditions?learner_id=L1")
    assert res.status_code == 200
    data = res.json()
    assert data["locked"] is True
    assert len(data["reasons"]) == 1
    assert data["reasons"][0]["status"] == "PRIOR_NODE_INCOMPLETE"
    assert data["reasons"][0]["prerequisite_skill"] == "c2"


def test_prerequisite_threshold_unlocks_node():
    # Pass node 1 to unlock node 2
    req = {"learner_id": "L1", "assessment_score": 90.0, "practical_pass": True}
    res = client.post("/nodes/n1/complete", json=req)
    assert "n2" in res.json()["unlocked_nodes"]

    # Verify via lock explanation
    res_lock = client.get("/nodes/n2/unlock-conditions?learner_id=L1")
    assert res_lock.json()["locked"] is False


def test_insufficient_proficiency_keeps_node_locked():
    # Pass node 1 but with just exactly 80.0
    req = {"learner_id": "L1", "assessment_score": 80.0, "practical_pass": True}
    client.post("/nodes/n1/complete", json=req)

    # Node 2 requires 0.8, which is met. But let's say it required 0.85:
    state_repo.db["prerequisites"]["c2"][0]["required_proficiency"] = 0.85

    res_lock = client.get("/nodes/n2/unlock-conditions?learner_id=L1")
    assert res_lock.json()["locked"] is True


def test_completion_is_idempotent():
    req = {"learner_id": "L1", "assessment_score": 90.0, "practical_pass": True}
    res1 = client.post("/nodes/n1/complete", json=req)
    assert len(res1.json()["skills_updated"]) == 2

    # Call again
    res2 = client.post("/nodes/n1/complete", json=req)
    # Should not update skills again
    assert len(res2.json()["skills_updated"]) == 0
    assert res2.json()["status"] == "COMPLETED"


def test_multiple_skills_taught_by_one_node_update_correctly():
    req = {"learner_id": "L1", "assessment_score": 90.0, "practical_pass": True}
    res = client.post("/nodes/n1/complete", json=req)
    skills = [s["skill_id"] for s in res.json()["skills_updated"]]
    assert "skill_a" in skills
    assert "skill_b" in skills


def test_existing_proficiency_is_not_blindly_overwritten():
    # Set high proficiency first
    state_repo.update_learner_proficiency("L1", "skill_a", 0.95, 0.8)

    req = {"learner_id": "L1", "assessment_score": 85.0, "practical_pass": True}
    res = client.post("/nodes/n1/complete", json=req)

    # Proficiency should remain 0.95 since 0.85 is lower
    prof = state_repo.get_learner_proficiency("L1", "skill_a")
    assert prof["proficiency"] == 0.95

    # Evidence is still preserved
    ev = state_repo.get_skill_evidence("L1", "skill_a")
    assert len(ev) == 1
    assert ev[0]["score"] == 0.85


def test_evidence_provenance_is_preserved():
    req = {"learner_id": "L1", "assessment_score": 85.0, "practical_pass": True}
    client.post("/nodes/n1/complete", json=req)
    ev = state_repo.get_skill_evidence("L1", "skill_a")
    assert ev[0]["source_type"] == "COURSE_COMPLETION"
    assert ev[0]["source_id"] == "n1"


def test_next_node_recommendation():
    # Before completion, n1 is IN_PROGRESS
    res = client.get("/paths/p1/next-node?learner_id=L1")
    assert res.json()["next_recommended_node"] == "n1"

    # Complete n1, which unlocks n2
    client.post(
        "/nodes/n1/complete",
        json={"learner_id": "L1", "assessment_score": 90.0, "practical_pass": True},
    )

    # Next node should be n2
    res2 = client.get("/paths/p1/next-node?learner_id=L1")
    assert res2.json()["next_recommended_node"] == "n2"


def test_next_node_recommendation_skips_completed_nodes():
    client.post(
        "/nodes/n1/complete",
        json={"learner_id": "L1", "assessment_score": 90.0, "practical_pass": True},
    )
    # Set n2 to COMPLETED
    node2 = state_repo.get_node("n2")
    node2.status = NodeStatus.COMPLETED
    state_repo.update_node(node2)
    # Unlock n3 manually to test recommendation skipping n2
    node3 = state_repo.get_node("n3")
    node3.status = NodeStatus.UNLOCKED
    state_repo.update_node(node3)

    res = client.get("/paths/p1/next-node?learner_id=L1")
    assert res.json()["next_recommended_node"] == "n3"


def test_recommendation_is_dependency_aware():
    # We set two unlocked nodes, n2 and a new node n4.
    node4 = PathNode(
        node_id="n4",
        path_id="p1",
        course_id="c4",
        sequence_order=4,
        status=NodeStatus.UNLOCKED,
    )
    state_repo.update_node(node4)

    client.post(
        "/nodes/n1/complete",
        json={"learner_id": "L1", "assessment_score": 90.0, "practical_pass": True},
    )

    # After completing n1, n2 unlocks.
    # n2 has order=2, n4 has order=4. n2 should be recommended.
    res = client.get("/paths/p1/next-node?learner_id=L1")
    assert res.json()["next_recommended_node"] == "n2"


def test_learner_isolation():
    req1 = {"learner_id": "L1", "assessment_score": 90.0, "practical_pass": True}
    client.post("/nodes/n1/complete", json=req1)

    # Learner L2 shouldn't have any evidence
    ev = state_repo.get_skill_evidence("L2", "skill_a")
    assert len(ev) == 0


def test_completion_failure_does_not_partially_mutate_progression():
    # Pass node 1 but fail practical
    req = {"learner_id": "L1", "assessment_score": 90.0, "practical_pass": False}
    client.post("/nodes/n1/complete", json=req)

    node1 = state_repo.get_node("n1")
    assert node1.status == NodeStatus.REMEDIATION

    node2 = state_repo.get_node("n2")
    assert node2.status == NodeStatus.LOCKED

    assert len(state_repo.get_skill_evidence("L1", "skill_a")) == 0
