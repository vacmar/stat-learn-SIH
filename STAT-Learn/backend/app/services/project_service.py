import uuid
from datetime import UTC, datetime

from app.repository import state_repo
from app.services import unlock_service


def submit_project(learner_id: str, project_id: str, artifact: str) -> dict:
    project = state_repo.get_project(project_id)
    if not project:
        raise ValueError("Project not found")

    submission_id = uuid.uuid4().hex

    submission = {
        "submission_id": submission_id,
        "learner_id": learner_id,
        "project_id": project_id,
        "artifact": artifact,
        "status": "SUBMITTED",
        "timestamp": datetime.now(UTC).isoformat(),
    }

    state_repo.save_project_submission(submission)
    return submission


def evaluate_project(project_id: str, evaluation: dict) -> dict:
    """
    Validates a structured AI evaluation against the project's requirements,
    derives the true passed status, and generates skill evidence if applicable.
    """
    submission_id = evaluation.get("submission_id")
    submission = state_repo.get_project_submission(str(submission_id))
    if not submission:
        raise ValueError("No submission found for this evaluation")

    if submission["project_id"] != project_id:
        raise ValueError("Submission does not belong to this project")

    learner_id = submission["learner_id"]

    # 1. Project Context
    project = state_repo.get_project(project_id)
    if not project:
        raise ValueError("Project not found")

    # Idempotency: if already passed, do nothing (skip evidence gen)
    # Note: A real implementation would check if THIS evaluation_id was already processed,
    # but since submission status mutates, we can rely on that for MVP idempotency.
    if submission.get("status") == "PASSED":
        return {
            "status": "PASSED",
            "feedback": submission.get("feedback", ""),
            "skills_updated": [],
            "unlocked_nodes": [],
            "next_recommended_node": None,
        }

    # 2. Score Validation
    raw_score = evaluation.get("score", 0.0)
    if not (0.0 <= raw_score <= 100.0):
        raise ValueError("Score must be between 0.0 and 100.0")

    # 3. Requirement Validation
    project_reqs = project.get("requirements", [])
    eval_reqs = {
        r["requirement_id"]: r["status"] for r in evaluation.get("requirements", [])
    }

    # Ensure all mandatory project requirements exist in the evaluation and are PASS
    backend_passed = True
    for req in project_reqs:
        if req.get("mandatory", False):
            req_id = req["requirement_id"]
            if req_id not in eval_reqs:
                raise ValueError(f"Mandatory requirement {req_id} was not evaluated")
            if eval_reqs[req_id] != "PASS":
                backend_passed = False

    # 4. Generate evaluation_id
    evaluation_id = uuid.uuid4().hex

    # 5. Update Submission State
    submission["status"] = "PASSED" if backend_passed else "NEEDS_REVISION"
    submission["score"] = raw_score
    # Flatten strengths/improvements into a generic feedback string or save as structured
    feedback = f"Strengths: {', '.join(evaluation.get('strengths', []))}. Improvements: {', '.join(evaluation.get('improvements', []))}."
    submission["feedback"] = feedback
    submission["evaluated_at"] = datetime.now(UTC).isoformat()
    submission["evaluation_id"] = evaluation_id

    state_repo.save_project_submission(submission)

    skills_updated = []
    unlocked_nodes = []
    next_node = None

    # 6. Evidence Generation (Only if passed)
    if backend_passed:
        valid_project_skills = set(project.get("taught_skills", []))

        for skill_eval in evaluation.get("skills_demonstrated", []):
            skill_id = skill_eval["skill_id"]
            score = skill_eval["score"]
            confidence = skill_eval["confidence"]

            # Validation bounds
            if not (0.0 <= score <= 1.0):
                raise ValueError(
                    f"Skill score {score} for {skill_id} is out of bounds [0.0, 1.0]"
                )
            if not (0.0 <= confidence <= 1.0):
                raise ValueError(
                    f"Skill confidence {confidence} for {skill_id} is out of bounds [0.0, 1.0]"
                )

            # Must belong to project
            if skill_id not in valid_project_skills:
                # Silently ignore or reject. We will reject.
                raise ValueError(f"Skill {skill_id} is not taught by this project")

            # Generate Evidence
            old_prof_obj = state_repo.get_learner_proficiency(learner_id, skill_id)
            old_prof = old_prof_obj["proficiency"]

            state_repo.record_skill_evidence(
                learner_id=learner_id,
                skill_id=skill_id,
                source_type="PROJECT_EVALUATION",
                source_id=evaluation_id,  # Must use evaluation_id!
                score=score,
                confidence=confidence,
                timestamp=submission["evaluated_at"],
            )

            # Fuse Proficiency (Phase 8 logic)
            new_prof = max(old_prof, score)
            state_repo.update_learner_proficiency(
                learner_id, skill_id, new_prof, confidence
            )

            skills_updated.append(
                {
                    "skill_id": skill_id,
                    "previous_proficiency": old_prof,
                    "new_proficiency": new_prof,
                }
            )

        unlocked_nodes = unlock_service.check_unlocks(learner_id, "p1")
        next_node = unlock_service.get_next_recommended_node(learner_id, "p1")

    return {
        "status": submission["status"],
        "feedback": feedback,
        "skills_updated": skills_updated,
        "unlocked_nodes": unlocked_nodes,
        "next_recommended_node": next_node,
    }
