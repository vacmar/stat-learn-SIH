from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.domain import LearningPath, NodeStatus, PathNode
from app.repository import state_repo

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    state_repo.db["paths"].clear()
    state_repo.db["nodes"].clear()
    state_repo.db["proficiency"].clear()
    state_repo.db["learner_profiles"]["L1"] = {"target_role": "role_de"}

    state_repo.db["target_roles"] = {
        "role_de": {
            "role_id": "role_de",
            "required_skills": {"skill_py": 0.8, "skill_dist": 0.8, "skill_cloud": 0.8},
        }
    }

    path_id = "p1"
    path = LearningPath(
        path_id=path_id,
        learner_id="L1",
        version=1,
        created_at=datetime.now(UTC).isoformat(),
        is_active=True,
    )
    state_repo.save_path(path)

    # Old path: c_py -> c_dist -> c_cloud
    node1 = PathNode(
        node_id="n1",
        path_id=path_id,
        course_id="c_py",
        sequence_order=1,
        status=NodeStatus.COMPLETED,
    )
    node2 = PathNode(
        node_id="n2",
        path_id=path_id,
        course_id="c_dist",
        sequence_order=2,
        status=NodeStatus.IN_PROGRESS,
    )
    node3 = PathNode(
        node_id="n3",
        path_id=path_id,
        course_id="c_cloud",
        sequence_order=3,
        status=NodeStatus.LOCKED,
    )

    # Restrict target role so the path doesn't "change" magically
    state_repo.db["target_roles"]["role_de"]["required_skills"] = {
        "skill_py": 0.8,
        "skill_dist": 0.8,
        "skill_cloud": 0.8,
    }

    state_repo.update_node(node1)
    state_repo.update_node(node2)
    state_repo.update_node(node3)


def test_no_state_change_no_new_path_version():
    req = {"learner_id": "L1"}
    res = client.post("/paths/p1/regenerate", json=req)
    assert res.status_code == 200
    data = res.json()
    assert data["changed"] is False
    assert data["path_id"] == "p1"
    assert data["version"] == 1


def test_completed_nodes_preserved_in_history_and_in_progress_preserved():
    # Complete some project that gives them stats proficiency
    state_repo.db["target_roles"]["role_de"]["required_skills"]["skill_stats"] = 0.8
    state_repo.update_learner_proficiency("L1", "skill_stats", 0.0, 0.9)
    req = {"learner_id": "L1"}
    res = client.post("/paths/p1/regenerate", json=req)
    data = res.json()
    assert data["changed"] is True

    nodes = data["nodes"]
    c_py_node = next(n for n in nodes if n["course_id"] == "c_py")
    assert c_py_node["status"] == "COMPLETED"

    c_dist_node = next(n for n in nodes if n["course_id"] == "c_dist")
    assert c_dist_node["status"] == "IN_PROGRESS"


def test_completed_nodes_not_duplicated():
    # If Python is completed, it should not appear again as LOCKED
    state_repo.db["target_roles"]["role_de"]["required_skills"]["skill_stats"] = 0.8
    state_repo.update_learner_proficiency("L1", "skill_stats", 0.0, 0.9)
    res = client.post("/paths/p1/regenerate", json={"learner_id": "L1"})
    nodes = res.json()["nodes"]

    py_nodes = [n for n in nodes if n["course_id"] == "c_py"]
    assert len(py_nodes) == 1


def test_new_prerequisite_recursively_inserted():
    state_repo.db["paths"]["p1"].is_active = False
    path_id = "p_fresh"
    state_repo.save_path(
        LearningPath(
            path_id=path_id, learner_id="L1", version=1, created_at="", is_active=True
        )
    )

    res = client.post(f"/paths/{path_id}/regenerate", json={"learner_id": "L1"})
    nodes = res.json()["nodes"]

    # We should have c_py, c_dist, c_cloud
    course_ids = [n["course_id"] for n in nodes]
    assert "c_py" in course_ids
    assert "c_dist" in course_ids

    # Check topological sort (prereq comes before dependent)
    assert course_ids.index("c_py") < course_ids.index("c_dist")
    assert course_ids.index("c_dist") < course_ids.index("c_cloud")


def test_mastered_prerequisite_not_inserted():
    state_repo.db["paths"]["p1"].is_active = False
    path_id = "p_fresh"
    state_repo.save_path(
        LearningPath(
            path_id=path_id, learner_id="L1", version=1, created_at="", is_active=True
        )
    )

    # Master python
    state_repo.update_learner_proficiency("L1", "skill_py", 1.0, 1.0)

    res = client.post(f"/paths/{path_id}/regenerate", json={"learner_id": "L1"})
    nodes = res.json()["nodes"]

    course_ids = [n["course_id"] for n in nodes]
    assert "c_py" not in course_ids
    assert "c_dist" in course_ids


def test_project_proficiency_change_alters_eligibility():
    # L1 masters 'cloud' from a project
    state_repo.update_learner_proficiency("L1", "skill_cloud", 1.0, 0.9)

    res = client.post("/paths/p1/regenerate", json={"learner_id": "L1"})
    data = res.json()
    assert data["changed"] is True

    nodes = data["nodes"]

    # Check changes facts
    changes = data["changes"]
    removed = [c["course_id"] for c in changes if c["type"] == "NODE_REMOVED"]
    assert "c_cloud" in removed


def test_old_path_remains_auditable_and_new_path_references_previous():
    state_repo.db["target_roles"]["role_de"]["required_skills"]["skill_sql"] = 0.8
    # No proficiency means c_sql is now required
    res = client.post("/paths/p1/regenerate", json={"learner_id": "L1"})
    data = res.json()
    new_path_id = data["path_id"]

    # Check old path
    old_path = state_repo.db["paths"]["p1"]
    assert old_path.is_active is False

    # Check new path references old
    assert data["previous_path_id"] == "p1"


def test_repeated_regeneration_idempotent():
    state_repo.update_learner_proficiency("L1", "skill_sql", 1.0, 0.9)  # trigger change
    res = client.post("/paths/p1/regenerate", json={"learner_id": "L1"})
    new_path_id = res.json()["path_id"]

    # Try again on new path with no state change
    res2 = client.post(f"/paths/{new_path_id}/regenerate", json={"learner_id": "L1"})
    assert res2.json()["changed"] is False
    assert res2.json()["path_id"] == new_path_id


def test_learner_isolation():
    res = client.post("/paths/p1/regenerate", json={"learner_id": "L2"})
    assert res.status_code == 400
    assert (
        "not the active path" in res.json()["detail"]
        or "No active path" in res.json()["detail"]
    )


def test_ranking_remains_dependency_aware():
    state_repo.db["paths"]["p1"].is_active = False
    path_id = "p_fresh"
    state_repo.save_path(
        LearningPath(
            path_id=path_id, learner_id="L1", version=1, created_at="", is_active=True
        )
    )
    res = client.post(f"/paths/{path_id}/regenerate", json={"learner_id": "L1"})
    nodes = res.json()["nodes"]
    course_ids = [n["course_id"] for n in nodes]
    # c_py must be before c_dist, and c_dist before c_cloud
    assert course_ids.index("c_py") < course_ids.index("c_dist")
    assert course_ids.index("c_dist") < course_ids.index("c_cloud")


def test_structured_change_facts_identify_added_removed():
    state_repo.db["paths"]["p1"].is_active = False
    path_id = "p_fresh"
    state_repo.save_path(
        LearningPath(
            path_id=path_id, learner_id="L1", version=1, created_at="", is_active=True
        )
    )
    res = client.post(f"/paths/{path_id}/regenerate", json={"learner_id": "L1"})
    new_id = res.json()["path_id"]

    # Now we master c_py
    state_repo.update_learner_proficiency("L1", "skill_py", 1.0, 0.9)
    res2 = client.post(f"/paths/{new_id}/regenerate", json={"learner_id": "L1"})
    changes = res2.json()["changes"]

    removed = [c["course_id"] for c in changes if c["type"] == "NODE_REMOVED"]
    assert "c_py" in removed


def test_failed_regeneration_no_partial_mutation():
    # If it fails, DB state should not have deactivated the old path
    res = client.post("/paths/p1/regenerate", json={"learner_id": "L2"})
    old_path = state_repo.db["paths"]["p1"]
    assert old_path.is_active is True
