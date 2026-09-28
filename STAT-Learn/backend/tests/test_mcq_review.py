"""Source-grounded MCQ drafts and human review."""

import json

import pytest
from fastapi.testclient import TestClient

from app.data.sampling_note import CHUNKS, DOCUMENT
from app.main import app
from app.services.mcq_generation import candidates_from_model, select_context, validate_candidate
from app.services.mcq_store import reset_memory

client = TestClient(app)
ADMIN = {"X-Statlearn-Demo-Actor": "training-admin"}
BODY = {
    "document_id": DOCUMENT.id,
    "competency_id": "stat-survey-methodology",
    "target_level": "L2",
    "count": 1,
}


@pytest.fixture(autouse=True)
def clean():
    reset_memory()
    yield
    reset_memory()


def test_document_and_chunks():
    assert DOCUMENT.status == "Ready"
    assert len(CHUNKS) >= 3
    chunks = select_context(DOCUMENT.id, "stat-survey-methodology")
    assert chunks
    with pytest.raises(Exception):
        select_context("missing", "stat-survey-methodology")


def _valid_raw(question="Which statement is supported by the coverage section?"):
    return json.dumps(
        {
            "question": question,
            "options": ["A frame gap", "A chart colour", "A font", "A press date"],
            "correct_option": "A frame gap",
            "explanation": "The coverage section describes missing dwellings.",
            "source_chunk_ids": ["chunk-coverage"],
        }
    )


def test_structural_validation():
    chunks = select_context(DOCUMENT.id, "stat-survey-methodology")
    good = candidates_from_model([_valid_raw()], chunks, "stat-survey-methodology", "L2")
    assert good[0]["origin"] == "model"
    with pytest.raises(Exception):
        validate_candidate(json.loads(_valid_raw()), set(), "stat-survey-methodology", "L2")
    bad = json.loads(_valid_raw())
    bad["options"] = ["only one"]
    with pytest.raises(Exception):
        validate_candidate(bad, {"chunk-coverage"}, "stat-survey-methodology", "L2")
    bad = json.loads(_valid_raw())
    bad["correct_option"] = "not listed"
    with pytest.raises(Exception):
        validate_candidate(bad, {"chunk-coverage"}, "stat-survey-methodology", "L2")
    bad = json.loads(_valid_raw())
    bad["source_chunk_ids"] = []
    with pytest.raises(Exception):
        validate_candidate(bad, {"chunk-coverage"}, "stat-survey-methodology", "L2")


def test_generate_failure_stores_nothing(monkeypatch):
    monkeypatch.setattr("app.api.admin_mcq.model_available", lambda: False)
    res = client.post("/admin/mcq/generate", headers=ADMIN, json=BODY)
    assert res.status_code == 503
    assert client.get("/admin/mcq-review", headers=ADMIN).json()["drafts"] == []


def test_generate_success_and_duplicate(monkeypatch):
    monkeypatch.setattr("app.api.admin_mcq.model_available", lambda: True)
    monkeypatch.setattr("app.api.admin_mcq.call_model", lambda _prompt: _valid_raw())
    first = client.post("/admin/mcq/generate", headers=ADMIN, json=BODY)
    assert first.status_code == 200
    assert first.json()["drafts"][0]["badge"] == "AI generated"
    assert first.json()["drafts"][0]["status"] == "DRAFT"
    second = client.post("/admin/mcq/generate", headers=ADMIN, json=BODY)
    assert second.status_code == 409


def test_demo_draft_is_not_labeled_as_model():
    res = client.post("/admin/mcq/demo-draft", headers=ADMIN, json=BODY)
    assert res.status_code == 200
    draft = res.json()["drafts"][0]
    assert draft["badge"] == "Demo-generated draft"
    assert draft["origin"] == "demo_draft"
    assert draft["evidence"][0]["text"]


def test_review_transitions_bank_and_audit():
    created = client.post("/admin/mcq/demo-draft", headers=ADMIN, json={**BODY, "count": 2})
    ids = [item["id"] for item in created.json()["drafts"]]
    approved = client.post(f"/admin/mcq/{ids[0]}/approve", headers=ADMIN)
    assert approved.status_code == 200
    assert approved.json()["question"]["status"] == "APPROVED"
    assert approved.json()["audit"][0]["actor"] == "training-admin"
    assert approved.json()["audit"][0]["previous_status"] == "DRAFT"
    rejected = client.post(f"/admin/mcq/{ids[1]}/reject", headers=ADMIN)
    assert rejected.status_code == 200
    assert rejected.json()["question"]["status"] == "REJECTED"
    again = client.post(f"/admin/mcq/{ids[0]}/reject", headers=ADMIN)
    assert again.status_code == 409
    bank = client.get("/admin/question-bank", headers=ADMIN).json()["questions"]
    bank_ids = [item["id"] for item in bank]
    assert ids[0] in bank_ids
    assert ids[1] not in bank_ids
    review_ids = [item["id"] for item in client.get("/admin/mcq-review", headers=ADMIN).json()["drafts"]]
    assert ids[0] not in review_ids
    assert ids[1] not in review_ids


def test_non_admin_cannot_approve():
    created = client.post("/admin/mcq/demo-draft", headers=ADMIN, json=BODY)
    question_id = created.json()["drafts"][0]["id"]
    denied = client.post(
        f"/admin/mcq/{question_id}/approve",
        headers={"X-Statlearn-Demo-Learner": "arun-kumar"},
    )
    assert denied.status_code == 403
    materials = client.get("/admin/materials")
    assert materials.status_code == 403
