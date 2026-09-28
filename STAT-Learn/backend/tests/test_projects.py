import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.domain import NodeStatus, PathNode
from app.repository import state_repo

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    state_repo.db["project_submissions"].clear()
    state_repo.db["evidence"].clear()
    state_repo.db["proficiency"].clear()

    node1 = PathNode(
        node_id="n1",
        path_id="p1",
        course_id="c1",
        sequence_order=1,
        status=NodeStatus.LOCKED,
    )
    state_repo.update_node(node1)

    state_repo.db["prerequisites"]["c1"] = [
        {"skill_id": "skill_py", "required_proficiency": 0.8}
    ]


def submit_test_project():
    req = {"learner_id": "L1", "artifact": "https://github.com/test"}
    res = client.post("/projects/proj_1/submit", json=req)
    return res.json()["submission_id"]


def create_eval_payload(sub_id, passed=True, score=90.0, reqs=None, skills=None):
    if reqs is None:
        reqs = [
            {
                "requirement_id": "req_fastapi",
                "status": "PASS",
                "evidence": "found fast",
            },
            {
                "requirement_id": "req_health",
                "status": "PASS",
                "evidence": "found health",
            },
            {"requirement_id": "req_json", "status": "PASS", "evidence": "found json"},
        ]
    if skills is None:
        skills = [{"skill_id": "skill_py", "score": 0.9, "confidence": 0.9}]
    return {
        "submission_id": sub_id,
        "score": score,
        "passed": passed,
        "requirements": reqs,
        "skills_demonstrated": skills,
        "strengths": ["Good"],
        "improvements": ["None"],
    }


def test_project_submission():
    sub_id = submit_test_project()
    assert sub_id is not None
    sub = state_repo.get_project_submission(sub_id)
    assert sub["learner_id"] == "L1"


def test_structured_evaluation_accepted():
    sub_id = submit_test_project()
    payload = create_eval_payload(sub_id)
    res = client.post("/projects/proj_1/evaluate", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "PASSED"
    assert len(res.json()["skills_updated"]) == 1


def test_missing_required_requirement_rejected():
    sub_id = submit_test_project()
    # Omitting 'req_json' which is mandatory
    reqs = [
        {"requirement_id": "req_fastapi", "status": "PASS", "evidence": "found fast"},
        {"requirement_id": "req_health", "status": "PASS", "evidence": "found health"},
    ]
    payload = create_eval_payload(sub_id, reqs=reqs)
    res = client.post("/projects/proj_1/evaluate", json=payload)
    assert res.status_code == 400
    assert "was not evaluated" in res.json()["detail"]


def test_mandatory_failed_requirement_no_progression():
    sub_id = submit_test_project()
    reqs = [
        {"requirement_id": "req_fastapi", "status": "PASS", "evidence": ""},
        {"requirement_id": "req_health", "status": "FAIL", "evidence": "missing"},
        {"requirement_id": "req_json", "status": "PASS", "evidence": ""},
    ]
    payload = create_eval_payload(sub_id, reqs=reqs)
    res = client.post("/projects/proj_1/evaluate", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "NEEDS_REVISION"
    assert len(res.json()["skills_updated"]) == 0


def test_high_score_with_failed_mandatory_no_progression():
    sub_id = submit_test_project()
    reqs = [
        {"requirement_id": "req_fastapi", "status": "PASS", "evidence": ""},
        {"requirement_id": "req_health", "status": "FAIL", "evidence": "missing"},
        {"requirement_id": "req_json", "status": "PASS", "evidence": ""},
    ]
    payload = create_eval_payload(sub_id, score=99.0, passed=True, reqs=reqs)
    res = client.post("/projects/proj_1/evaluate", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "NEEDS_REVISION"  # Backend overrides


def test_invalid_skill_id_rejected():
    sub_id = submit_test_project()
    skills = [{"skill_id": "skill_unknown", "score": 0.9, "confidence": 0.9}]
    payload = create_eval_payload(sub_id, skills=skills)
    res = client.post("/projects/proj_1/evaluate", json=payload)
    assert res.status_code == 400
    assert "is not taught by this project" in res.json()["detail"]


def test_score_out_of_bounds_rejected():
    sub_id = submit_test_project()
    skills = [{"skill_id": "skill_py", "score": 1.5, "confidence": 0.9}]
    payload = create_eval_payload(sub_id, skills=skills)
    res = client.post("/projects/proj_1/evaluate", json=payload)
    assert res.status_code == 400
    assert "out of bounds" in res.json()["detail"]


def test_confidence_out_of_bounds_rejected():
    sub_id = submit_test_project()
    skills = [{"skill_id": "skill_py", "score": 0.9, "confidence": -0.1}]
    payload = create_eval_payload(sub_id, skills=skills)
    res = client.post("/projects/proj_1/evaluate", json=payload)
    assert res.status_code == 400
    assert "out of bounds" in res.json()["detail"]


def test_passed_evaluation_creates_evidence_with_evaluation_id():
    sub_id = submit_test_project()
    payload = create_eval_payload(sub_id)
    res = client.post("/projects/proj_1/evaluate", json=payload)
    assert res.status_code == 200

    sub = state_repo.get_project_submission(sub_id)
    eval_id = sub["evaluation_id"]

    ev = state_repo.get_skill_evidence("L1", "skill_py")
    assert len(ev) == 1
    assert ev[0]["source_type"] == "PROJECT_EVALUATION"
    assert ev[0]["source_id"] == eval_id


def test_ai_says_passed_true_but_mandatory_fails():
    sub_id = submit_test_project()
    reqs = [
        {"requirement_id": "req_fastapi", "status": "PASS", "evidence": ""},
        {"requirement_id": "req_health", "status": "FAIL", "evidence": ""},
        {"requirement_id": "req_json", "status": "PASS", "evidence": ""},
    ]
    # AI lies
    payload = create_eval_payload(sub_id, passed=True, score=95.0, reqs=reqs)
    res = client.post("/projects/proj_1/evaluate", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "NEEDS_REVISION"


def test_ai_says_passed_false_but_mandatory_passes():
    sub_id = submit_test_project()
    # AI lies the other way
    payload = create_eval_payload(sub_id, passed=False, score=85.0)
    res = client.post("/projects/proj_1/evaluate", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "PASSED"


def test_retrying_evaluation_is_idempotent():
    sub_id = submit_test_project()
    payload = create_eval_payload(sub_id)
    client.post("/projects/proj_1/evaluate", json=payload)

    ev_count = len(state_repo.get_skill_evidence("L1", "skill_py"))

    # Retry
    res = client.post("/projects/proj_1/evaluate", json=payload)
    assert res.status_code == 200

    # Evidence should not duplicate
    ev_count_after = len(state_repo.get_skill_evidence("L1", "skill_py"))
    assert ev_count == ev_count_after
