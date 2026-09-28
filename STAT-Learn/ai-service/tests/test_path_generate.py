"""Unit tests for profile-aware path generation (mock provider)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.structured import PathGenerateRequest
from app.services.path_generator import mock_generate_pathway

client = TestClient(app)


def test_android_profile_gets_mobile_stages():
    req = PathGenerateRequest(
        learner_id="L1",
        name="Test User",
        target_role="Android Developer",
        target_role_id="role_other",
        custom_role_title="Android Developer",
        target_domain="React Native",
        experience_level="Beginner",
        known_skills=["React.js", "Python", "Java", "SQL"],
        interests=["UI/UX", "Mobile Responsiveness"],
        learning_style="mixed",
        weekly_time=10,
        goals=["Become a Android Developer"],
    )
    path = mock_generate_pathway(req)
    names = [s.course_name.lower() for s in path.stages]
    assert any("react native" in n or "android" in n for n in names)
    assert not any(n.strip() in {"python basics", "sql basics"} for n in names)
    assert path.capstone is not None
    assert "fastapi" not in path.capstone.title.lower()
    assert (
        "react native" in path.capstone.description.lower()
        or "mobile" in path.capstone.title.lower()
    )


def test_arbitrary_other_role_is_not_forced_mobile():
    req = PathGenerateRequest(
        learner_id="L_sec",
        name="Sam",
        target_role="Security Analyst",
        target_role_id="role_other",
        custom_role_title="Security Analyst",
        target_domain="Fintech",
        experience_level="Beginner",
        prior_experience="Helpdesk for 1 year",
        known_skills=["Networking", "Linux"],
        interests=["Threat hunting", "SIEM"],
        learning_style="hands_on",
        weekly_time=10,
        goals=["Become a Security Analyst"],
    )
    path = mock_generate_pathway(req)
    joined = " ".join(s.course_name.lower() for s in path.stages)
    assert "security analyst" in joined
    assert "react native" not in joined
    assert "python basics" not in joined
    assert path.capstone is not None
    assert "security analyst" in path.capstone.title.lower()
    assert "fastapi" not in path.capstone.description.lower()


def test_backend_profile_gets_api_stages():
    req = PathGenerateRequest(
        learner_id="L2",
        target_role="Backend Developer",
        target_role_id="role_be",
        target_domain="APIs",
        experience_level="Beginner",
        known_skills=[],
        interests=[],
        weekly_time=10,
        goals=["Become a Backend Developer"],
    )
    path = mock_generate_pathway(req)
    names = " ".join(s.course_name.lower() for s in path.stages)
    assert "python" in names or "fastapi" in names or "rest" in names
    assert path.capstone is not None
    assert (
        "fastapi" in path.capstone.description.lower()
        or "api" in path.capstone.title.lower()
    )


def test_data_profile_differs_from_mobile():
    mobile = mock_generate_pathway(
        PathGenerateRequest(
            target_role="Android Developer",
            target_domain="React Native",
            target_role_id="role_other",
        )
    )
    data = mock_generate_pathway(
        PathGenerateRequest(
            target_role="Data Engineer",
            target_domain="Warehouses",
            target_role_id="role_de",
        )
    )
    assert [s.course_name for s in mobile.stages] != [
        s.course_name for s in data.stages
    ]


@pytest.mark.asyncio
async def test_path_generate_endpoint_mock():
    # Force mock via env is already default in tests if no key; call endpoint
    resp = client.post(
        "/path/generate",
        json={
            "learner_id": "L3",
            "target_role": "Android Developer",
            "target_role_id": "role_other",
            "target_domain": "React Native",
            "known_skills": ["React.js"],
            "weekly_time": 10,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["stages"]
    assert body["capstone"]["title"]
