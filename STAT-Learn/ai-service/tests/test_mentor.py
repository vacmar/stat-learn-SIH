import pytest

from app.tools.backend_client import backend_client
from app.tools.registry import evaluate_project


@pytest.mark.asyncio
async def test_evaluate_project_tool(monkeypatch):
    async def mock_safe_post(endpoint, payload, fallback_data):
        assert "proj_1" in endpoint
        assert payload["score"] == 95.0
        assert len(payload["requirements"]) == 1
        return {
            "status": "PASSED",
            "feedback": "Good job",
            "skills_updated": [{"skill_id": "skill_py"}],
            "unlocked_nodes": ["n1"],
            "next_recommended_node": "n2",
        }

    monkeypatch.setattr(backend_client, "_safe_post", mock_safe_post)

    res = await evaluate_project.ainvoke(
        {
            "submission_id": "sub_1",
            "project_id": "proj_1",
            "score": 95.0,
            "passed": True,
            "requirements": [
                {"requirement_id": "req_fastapi", "status": "PASS", "evidence": "good"}
            ],
            "skills_demonstrated": [
                {"skill_id": "skill_py", "score": 0.9, "confidence": 0.9}
            ],
            "strengths": ["Excellent architecture."],
            "improvements": [],
        }
    )

    assert res["status"] == "PASSED"
    assert "n1" in res["unlocked_nodes"]
