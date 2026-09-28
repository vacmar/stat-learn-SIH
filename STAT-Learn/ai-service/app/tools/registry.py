from typing import Any

from langchain_core.tools import BaseTool, tool

from app.tools.backend_client import backend_client
from app.tools.schemas import (
    CalculateSkillGapsArgs,
    CheckUnlockConditionsArgs,
    CompleteLearningNodeArgs,
    EvaluateProjectArgs,
    ExplainPathwayChangeArgs,
    FindCoursesForSkillArgs,
    FindProjectsForSkillsArgs,
    GenerateCandidatePathsArgs,
    GetConversationContextArgs,
    GetCurrentSkillStateArgs,
    GetLearnerProfileArgs,
    GetLearningNodeStateArgs,
    GetLessonContextArgs,
    GetPrerequisitesArgs,
    GetTargetRequirementsArgs,
    GetWeakConceptsArgs,
    RankCandidatePathsArgs,
    RecordAssessmentResultArgs,
    RecordMistakeArgs,
    UpdateSkillEvidenceArgs,
)


@tool(args_schema=GetLearnerProfileArgs)
async def get_learner_profile(learner_id: str) -> dict[str, Any]:
    """Retrieve the core profile, enrolled career role, and active learning path for a learner."""
    return await backend_client.get_learner_profile(learner_id)


@tool(args_schema=GetCurrentSkillStateArgs)
async def get_current_skill_state(learner_id: str) -> list[dict[str, Any]]:
    """Retrieve the verified skill proficiency levels and confidence ratings for a learner."""
    return await backend_client.get_current_skill_state(learner_id)


@tool(args_schema=GetTargetRequirementsArgs)
async def get_target_requirements(role_id: str) -> list[dict[str, Any]]:
    """Fetch the mandatory and recommended skills, weights, and proficiency targets for a career role."""
    return await backend_client.get_target_requirements(role_id)


@tool(args_schema=CalculateSkillGapsArgs)
async def calculate_skill_gaps(learner_id: str, role_id: str) -> list[dict[str, Any]]:
    """Calculate the exact mathematical gaps between a learner's current verified skills and the goal requirements."""
    return await backend_client.calculate_skill_gaps(learner_id, role_id)


@tool(args_schema=GetPrerequisitesArgs)
async def get_prerequisites(course_id: str) -> list[dict[str, Any]]:
    """Get mandatory and optional prerequisite courses required before taking a specified course."""
    return await backend_client.get_prerequisites(course_id)


@tool(args_schema=FindCoursesForSkillArgs)
async def find_courses_for_skill(skill_id: str) -> list[dict[str, Any]]:
    """Locate available courses in the curriculum mapped to teaching a specific skill."""
    return await backend_client.find_courses_for_skill(skill_id)


@tool(args_schema=FindProjectsForSkillsArgs)
async def find_projects_for_skills(skill_ids: list[str]) -> list[dict[str, Any]]:
    """Locate practical capstone or portfolio projects covering a list of target skills."""
    return await backend_client.find_projects_for_skills(skill_ids)


@tool(args_schema=GenerateCandidatePathsArgs)
async def generate_candidate_paths(
    learner_id: str, role_id: str
) -> list[dict[str, Any]]:
    """Generate viable course sequence paths leading to the target role while satisfying prerequisites."""
    return await backend_client.generate_candidate_paths(learner_id, role_id)


@tool(args_schema=RankCandidatePathsArgs)
async def rank_candidate_paths(
    candidate_paths: list[dict[str, Any]], role_id: str | None = None
) -> list[dict[str, Any]]:
    """Rank candidate pathways based on skill-gap reduction, time efficiency, and difficulty fit."""
    return await backend_client.rank_candidate_paths(candidate_paths, role_id)


@tool(args_schema=GetLearningNodeStateArgs)
async def get_learning_node_state(node_id: str) -> dict[str, Any]:
    """Retrieve detailed state for a learning node including current module, concept, progress %, and mastery score."""
    return await backend_client.get_learning_node_state(node_id)


@tool(args_schema=GetConversationContextArgs)
async def get_conversation_context(
    conversation_id: str, limit: int | None = 10
) -> dict[str, Any]:
    """Retrieve rolling summary and recent messages for an active learning node conversation."""
    return await backend_client.get_conversation_context(
        conversation_id, limit=limit or 10
    )


@tool(args_schema=GetWeakConceptsArgs)
async def get_weak_concepts(learner_id: str, node_id: str) -> list[dict[str, Any]]:
    """Retrieve unresolved exercises, mistake patterns, and weak concepts requiring targeted remediation."""
    return await backend_client.get_weak_concepts(learner_id, node_id)


@tool(args_schema=RecordAssessmentResultArgs)
async def record_assessment_result(
    learner_id: str, assessment_id: str, score: float, passed: bool
) -> dict[str, Any]:
    """Record an official assessment quiz score and pass/fail evaluation into the database."""
    return await backend_client.record_assessment_result(
        learner_id, assessment_id, score, passed
    )


@tool(args_schema=UpdateSkillEvidenceArgs)
async def update_skill_evidence(
    learner_id: str, skill_id: str, score: float, source_type: str = "PRACTICAL"
) -> dict[str, Any]:
    """Submit structured evidence for a skill (e.g. from practical coding exercises or project evaluations)."""
    return await backend_client.update_skill_evidence(
        learner_id, skill_id, score, source_type
    )


@tool(args_schema=CheckUnlockConditionsArgs)
async def check_unlock_conditions(learner_id: str, node_id: str) -> dict[str, Any]:
    """Check if all prerequisite courses and mastery thresholds are satisfied to unlock a downstream node."""
    return await backend_client.check_unlock_conditions(learner_id, node_id)


@tool(args_schema=CompleteLearningNodeArgs)
async def complete_learning_node(
    node_id: str, assessment_score: float, practical_pass: bool
) -> dict[str, Any]:
    """Authoritatively transition a node to COMPLETED when lessons, exercises, and assessments meet the threshold."""
    return await backend_client.complete_learning_node(
        node_id, assessment_score, practical_pass
    )


@tool(args_schema=GetLessonContextArgs)
async def get_lesson_context(node_id: str) -> dict[str, Any]:
    """Retrieve structured pedagogical context for a node including lessons, exercises, and hints."""
    return await backend_client.get_lesson_context(node_id)


@tool(args_schema=RecordMistakeArgs)
async def record_mistake(
    learner_id: str, node_id: str, concept: str, description: str
) -> dict[str, Any]:
    """Record a conceptual mistake made by the learner for future remediation."""
    return await backend_client.record_mistake(
        learner_id, node_id, concept, description
    )


@tool(args_schema=EvaluateProjectArgs)
async def evaluate_project(
    submission_id: str,
    project_id: str,
    score: float,
    passed: bool,
    requirements: list[dict],
    skills_demonstrated: list[dict],
    strengths: list[str],
    improvements: list[str],
) -> dict[str, Any]:
    """Evaluate a project submission against requirements. Triggers backend validation."""
    payload = {
        "submission_id": submission_id,
        "score": score,
        "passed": passed,
        "requirements": requirements,
        "skills_demonstrated": skills_demonstrated,
        "strengths": strengths,
        "improvements": improvements,
    }
    return await backend_client.evaluate_project(project_id, payload)


@tool(args_schema=ExplainPathwayChangeArgs)
async def explain_pathway_change(
    old_path_id: str,
    new_path_id: str,
    changes: list[dict],
    proficiency_changes: list[dict],
) -> dict[str, Any]:
    """
    Explain the reasons for a pathway change using strictly the provided backend facts.
    Returns a human-readable explanation based only on the facts.
    """
    # For MVP, just return a structured reflection of what we would say
    if not changes and not proficiency_changes:
        return {
            "explanation": "Your path remains unchanged as there were no new eligible courses or mastered skills."
        }

    explanation = []
    for p in proficiency_changes:
        explanation.append(
            f"Your proficiency in {p.get('skill_id')} changed from {p.get('previous')} to {p.get('current')}."
        )

    for c in changes:
        if c.get("type") == "NODE_REMOVED":
            explanation.append(
                f"We removed {c.get('course_id')} because you mastered the prerequisites."
            )
        elif c.get("type") == "NODE_ADDED":
            explanation.append(
                f"We added {c.get('course_id')} because you are now eligible for it."
            )

    return {"explanation": " ".join(explanation)}


ALL_TOOLS: list[BaseTool] = [
    get_learner_profile,
    get_current_skill_state,
    get_target_requirements,
    calculate_skill_gaps,
    get_prerequisites,
    find_courses_for_skill,
    find_projects_for_skills,
    generate_candidate_paths,
    rank_candidate_paths,
    get_learning_node_state,
    get_conversation_context,
    get_weak_concepts,
    get_lesson_context,
    record_mistake,
    record_assessment_result,
    update_skill_evidence,
    check_unlock_conditions,
    complete_learning_node,
    evaluate_project,
    explain_pathway_change,
]

TOOLS_BY_NAME: dict[str, BaseTool] = {
    tool_inst.name: tool_inst for tool_inst in ALL_TOOLS
}
