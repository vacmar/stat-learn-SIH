from app.services import verification_service


def test_fusion_weights():
    verified = verification_service.fuse_verified_proficiency(
        {"assessment": 1.0, "practical": 1.0, "evidence": 1.0, "coursework": 1.0}
    )
    assert verified == 1.0

    half = verification_service.fuse_verified_proficiency(
        {"assessment": 0.5, "practical": 0.5, "evidence": 0.5, "coursework": 0.5}
    )
    assert half == 0.5


def test_verification_flow_with_discrepancy():
    from app.models.domain import Learner
    from app.repository import state_repo

    learner = Learner(
        learner_id="lv1",
        account_id="acc1",
        name="Test",
        self_reported_proficiency={"skill_py": 0.9},
        created_at="2024-01-01T00:00:00+00:00",
        updated_at="2024-01-01T00:00:00+00:00",
    )
    state_repo.create_learner(learner)

    session = verification_service.start_verification("lv1", "skill_py")
    assert session["claimed_proficiency"] == 0.9

    result = verification_service.submit_verification(
        "lv1",
        "skill_py",
        assessment=0.2,
        practical=0.2,
        evidence=0.1,
        coursework=0.1,
    )
    assert result["discrepancy"] is True
    assert result["verified_proficiency"] < result["claimed_proficiency"]

    stored = verification_service.get_verification_result("lv1", "skill_py")
    assert stored["skill_id"] == "skill_py"
