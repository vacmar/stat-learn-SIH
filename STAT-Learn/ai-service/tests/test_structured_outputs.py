from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.models.structured import (
    PathwayExplanation,
    PathwayStage,
    ProjectMentorFeedback,
    TutorResponse,
)


def test_tutor_response_model():
    res = TutorResponse(
        content="Decorators allow function wrapping.",
        concept_focus="Higher-Order Functions",
        check_question="Can you define a function that takes another function?",
        recommended_action="practice_exercise",
        remediation_needed=False,
        tools_used=["get_learning_node_state"],
    )
    assert res.content.startswith("Decorators")
    assert len(res.tools_used) == 1


def test_pathway_explanation_model():
    stage = PathwayStage(
        stage_number=1,
        course_name="Introduction to Python",
        rationale="Builds language syntax foundations",
        target_skills=["Python"],
    )
    explanation = PathwayExplanation(
        summary="Optimal pathway for Data Engineer",
        target_role="Data Engineer",
        stages=[stage],
        gap_analysis_summary="Covers 4 major skill gaps",
        estimated_total_hours=35.0,
        tools_used=["calculate_skill_gaps", "rank_candidate_paths"],
    )
    assert len(explanation.stages) == 1
    assert explanation.estimated_total_hours == 35.0


def test_project_mentor_feedback_model():
    feedback = ProjectMentorFeedback(
        project_title="Real-time ETL Stream Processor",
        passed=True,
        score=0.92,
        strengths=["Robust consumer retry logic"],
        areas_for_improvement=["Optimize batch flush interval"],
        next_milestone="Deploy to staging",
        tools_used=["update_skill_evidence"],
    )
    assert feedback.passed is True
    assert feedback.score == 0.92


def test_api_chat_endpoints():
    # Set provider to mock for API client testing
    settings.llm_provider = "mock"

    client = TestClient(app)

    # Test /chat/tutor
    tutor_payload = {
        "message": "Explain closures",
        "learner_id": "learner_test",
        "node_id": "node_py_01",
    }
    resp = client.post("/chat/tutor", json=tutor_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "message" in data
    assert data["persona"] == "tutor"
    assert data["structured"] is not None

    # Test /chat/pathway-explanation
    pathway_payload = {
        "message": "Why this path?",
        "learner_id": "learner_test",
        "role_id": "Data Engineer",
    }
    resp = client.post("/chat/pathway-explanation", json=pathway_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["persona"] == "pathway_reasoner"

    # Test /chat/project-mentor
    mentor_payload = {
        "message": "Review my solution",
        "learner_id": "learner_test",
        "project_id": "proj_etl_01",
    }
    resp = client.post("/chat/project-mentor", json=mentor_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["persona"] == "project_mentor"
