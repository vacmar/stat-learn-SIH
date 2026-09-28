from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api.auth import get_password_hash, verify_password
from app.main import app

client = TestClient(app)


def test_password_hashing():
    pw = "secret123"
    hashed = get_password_hash(pw)
    assert hashed != pw
    assert verify_password(pw, hashed)
    assert not verify_password("wrong", hashed)


@patch("app.api.auth.state_repo.create_account")
@patch("app.api.auth.state_repo.create_learner")
@patch("app.api.auth.state_repo.get_account_by_email")
@patch("app.api.auth.state_repo.get_account_by_id")
@patch("app.api.auth.state_repo.get_learner_by_account")
def test_signup_and_login(
    mock_get_learner_by_account,
    mock_get_account_by_id,
    mock_get_account_by_email,
    mock_create_learner,
    mock_create_account,
):
    # Setup mock behavior
    mock_db = {}
    mock_learner_db = {}

    def mock_get_email(email):
        return next((acc for acc in mock_db.values() if acc.email == email), None)

    def mock_create_acc(acc):
        mock_db[acc.account_id] = acc

    def mock_create_lrn(lrn):
        mock_learner_db[lrn.account_id] = lrn

    def mock_get_acc_id(acc_id):
        return mock_db.get(acc_id)

    def mock_get_lrn_by_acc(acc_id):
        return mock_learner_db.get(acc_id)

    mock_get_account_by_email.side_effect = mock_get_email
    mock_create_account.side_effect = mock_create_acc
    mock_create_learner.side_effect = mock_create_lrn
    mock_get_account_by_id.side_effect = mock_get_acc_id
    mock_get_learner_by_account.side_effect = mock_get_lrn_by_acc

    # Attempt signup
    res = client.post(
        "/auth/signup",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert res.status_code == 200
    data = res.json()
    assert "account_id" in data
    assert "learner_id" in data

    # Duplicate signup
    res_dup = client.post(
        "/auth/signup",
        json={
            "name": "Test User 2",
            "email": "test@example.com",
            "password": "password123",
        },
    )
    assert res_dup.status_code == 409

    # Login
    res_login = client.post(
        "/auth/login", json={"email": "test@example.com", "password": "password123"}
    )
    assert res_login.status_code == 200

    # Check /me
    res_me = client.get("/auth/me", cookies=res_login.cookies)
    assert res_me.status_code == 200
    assert res_me.json()["email"] == "test@example.com"

    # Logout
    res_logout = client.post("/auth/logout", cookies=res_login.cookies)
    assert res_logout.status_code == 200

    # Check /me again
    res_me2 = client.get("/auth/me", cookies=res_login.cookies)
    assert res_me2.status_code == 401
