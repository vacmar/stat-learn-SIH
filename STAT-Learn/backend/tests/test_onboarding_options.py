from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_onboarding_options_include_styles_and_other_role():
    res = client.get("/onboarding/")
    assert res.status_code == 200
    data = res.json()
    role_ids = {r["id"] for r in data["roles"]}
    assert "role_other" in role_ids
    assert "role_fe" in role_ids
    assert len(data["learning_styles"]) >= 4
    assert 10 in data["weekly_time_options"]
    assert data["role_titles"]["role_be"] == "Backend Developer"
