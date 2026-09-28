import uuid
from datetime import UTC, datetime
from typing import Any

from app.repository import state_repo

FUSION_WEIGHTS = {
    "assessment": 0.45,
    "practical": 0.25,
    "evidence": 0.15,
    "coursework": 0.15,
}

DISCREPANCY_THRESHOLD = 0.2


def fuse_verified_proficiency(signals: dict[str, float]) -> float:
    total = 0.0
    for key, weight in FUSION_WEIGHTS.items():
        total += weight * float(signals.get(key, 0.0))
    return round(min(1.0, max(0.0, total)), 4)


def start_verification(learner_id: str, skill_id: str) -> dict[str, Any]:
    learner = state_repo.get_learner(learner_id)
    claimed = 0.0
    if learner and learner.self_reported_proficiency:
        claimed = float(learner.self_reported_proficiency.get(skill_id, 0.0))

    session_id = uuid.uuid4().hex
    session = {
        "session_id": session_id,
        "learner_id": learner_id,
        "skill_id": skill_id,
        "status": "IN_PROGRESS",
        "claimed_proficiency": claimed,
        "signals": {},
        "started_at": datetime.now(UTC).isoformat(),
        "submitted_at": None,
        "result": None,
    }
    state_repo.save_verification_session(session_id, session)
    return session


def submit_verification(
    learner_id: str,
    skill_id: str,
    *,
    assessment: float,
    practical: float,
    evidence: float | None = None,
    coursework: float | None = None,
) -> dict[str, Any]:
    session = state_repo.get_verification_session_for_skill(learner_id, skill_id)
    if not session or session.get("status") != "IN_PROGRESS":
        raise ValueError("No active verification session for this skill")

    if evidence is None:
        records = state_repo.get_skill_evidence(learner_id, skill_id)
        evidence = max((r["score"] for r in records), default=0.0)
    if coursework is None:
        coursework = state_repo.get_learner_proficiency(learner_id, skill_id)[
            "proficiency"
        ]

    signals = {
        "assessment": min(1.0, max(0.0, assessment)),
        "practical": min(1.0, max(0.0, practical)),
        "evidence": min(1.0, max(0.0, evidence)),
        "coursework": min(1.0, max(0.0, coursework)),
    }
    verified = fuse_verified_proficiency(signals)
    claimed = float(session.get("claimed_proficiency", 0.0))
    delta = abs(claimed - verified)
    confidence = round(
        min(1.0, 0.5 + len(state_repo.get_skill_evidence(learner_id, skill_id)) * 0.1),
        4,
    )
    discrepancy = delta >= DISCREPANCY_THRESHOLD

    result = {
        "skill_id": skill_id,
        "claimed_proficiency": claimed,
        "verified_proficiency": verified,
        "confidence": confidence,
        "discrepancy": discrepancy,
        "discrepancy_delta": round(delta, 4),
        "signals": signals,
        "fusion_weights": FUSION_WEIGHTS,
    }

    session["signals"] = signals
    session["status"] = "COMPLETED"
    session["submitted_at"] = datetime.now(UTC).isoformat()
    session["result"] = result
    state_repo.save_verification_session(session["session_id"], session)

    state_repo.record_skill_evidence(
        learner_id=learner_id,
        skill_id=skill_id,
        source_type="VERIFICATION",
        source_id=session["session_id"],
        score=verified,
        confidence=confidence,
        timestamp=session["submitted_at"],
    )

    old = state_repo.get_learner_proficiency(learner_id, skill_id)
    state_repo.update_learner_proficiency(
        learner_id,
        skill_id,
        max(old["proficiency"], verified),
        confidence,
    )

    return result


def get_verification_result(learner_id: str, skill_id: str) -> dict[str, Any]:
    session = state_repo.get_verification_session_for_skill(learner_id, skill_id)
    if not session:
        raise ValueError("Verification session not found")
    if session.get("status") != "COMPLETED" or not session.get("result"):
        raise ValueError("Verification not yet completed")
    return session["result"]
