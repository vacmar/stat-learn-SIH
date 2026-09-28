from typing import Any

from pydantic import BaseModel, Field


class GetLearnerProfileArgs(BaseModel):
    learner_id: str = Field(description="Unique identifier of the learner")


class GetCurrentSkillStateArgs(BaseModel):
    learner_id: str = Field(description="Unique identifier of the learner")


class GetTargetRequirementsArgs(BaseModel):
    role_id: str = Field(description="Unique identifier of the career role")


class CalculateSkillGapsArgs(BaseModel):
    learner_id: str = Field(description="Unique identifier of the learner")
    role_id: str = Field(description="Target career role identifier")


class GetPrerequisitesArgs(BaseModel):
    course_id: str = Field(
        description="Identifier of the course to inspect prerequisites for"
    )


class FindCoursesForSkillArgs(BaseModel):
    skill_id: str = Field(
        description="Identifier of the skill to find covering courses for"
    )


class FindProjectsForSkillsArgs(BaseModel):
    skill_ids: list[str] = Field(
        description="List of skill IDs to locate suitable projects for"
    )


class GenerateCandidatePathsArgs(BaseModel):
    learner_id: str = Field(description="Unique identifier of the learner")
    role_id: str = Field(description="Target role identifier")


class RankCandidatePathsArgs(BaseModel):
    candidate_paths: list[dict[str, Any]] = Field(
        description="List of candidate learning path structures"
    )
    role_id: str | None = Field(
        default=None, description="Optional target role for gap reduction weighting"
    )


class GetLearningNodeStateArgs(BaseModel):
    node_id: str = Field(description="Unique identifier of the path learning node")


class GetConversationContextArgs(BaseModel):
    conversation_id: str = Field(
        description="Unique identifier of the conversation session"
    )
    limit: int | None = Field(
        default=10, description="Maximum number of recent messages to retrieve"
    )


class GetWeakConceptsArgs(BaseModel):
    learner_id: str = Field(description="Unique identifier of the learner")
    node_id: str = Field(
        description="Path node identifier to check unresolved or weak concepts for"
    )


class RecordAssessmentResultArgs(BaseModel):
    learner_id: str = Field(description="Unique identifier of the learner")
    assessment_id: str = Field(description="Unique identifier of the assessment")
    score: float = Field(
        description="Numerical score achieved (0.0 to 1.0 or percentage)"
    )
    passed: bool = Field(description="Whether the score meets the passing threshold")


class UpdateSkillEvidenceArgs(BaseModel):
    learner_id: str = Field(description="Unique identifier of the learner")
    skill_id: str = Field(description="Unique identifier of the skill")
    score: float = Field(description="Score or evidence rating (0.0 to 1.0)")
    source_type: str = Field(
        default="PRACTICAL",
        description="Source type: ASSESSMENT, PRACTICAL, COURSEWORK, or PROJECT",
    )


class CheckUnlockConditionsArgs(BaseModel):
    learner_id: str = Field(description="Unique identifier of the learner")
    node_id: str = Field(description="Target node to evaluate unlock prerequisites for")


class CompleteLearningNodeArgs(BaseModel):
    node_id: str = Field(
        description="Unique identifier of the node to transition to COMPLETED"
    )
    assessment_score: float = Field(description="Final assessment score achieved")
    practical_pass: bool = Field(
        description="Whether practical implementation task was passed"
    )


class GetLessonContextArgs(BaseModel):
    node_id: str = Field(
        description="Unique identifier of the path learning node to fetch pedagogical content for"
    )


class RecordMistakeArgs(BaseModel):
    learner_id: str = Field(description="Unique identifier of the learner")
    node_id: str = Field(description="Path node identifier")
    concept: str = Field(
        description="The underlying concept the learner struggled with (e.g. 'functools.wraps')"
    )
    description: str = Field(
        description="Detailed description of the mistake or misunderstanding"
    )


class RequirementEvaluation(BaseModel):
    requirement_id: str = Field(
        description="Unique identifier of the project requirement"
    )
    status: str = Field(description="PASS, FAIL, or PARTIAL")
    evidence: str = Field(
        description="Specific evidence from the artifact justifying the status"
    )


class SkillDemonstration(BaseModel):
    skill_id: str = Field(description="Unique identifier of the skill demonstrated")
    score: float = Field(description="Numerical score (0.0 to 1.0)")
    confidence: float = Field(description="Confidence in this assessment (0.0 to 1.0)")


class EvaluateProjectArgs(BaseModel):
    submission_id: str = Field(
        description="Unique identifier of the learner's submission"
    )
    project_id: str = Field(description="Unique identifier of the project")
    score: float = Field(description="Overall project score (0.0 to 100.0)")
    passed: bool = Field(
        description="Informational flag indicating if the project passed (backend determines final)"
    )
    requirements: list[RequirementEvaluation] = Field(
        description="Evaluation of each specific project requirement"
    )
    skills_demonstrated: list[SkillDemonstration] = Field(
        description="Specific skills demonstrated and their scores"
    )
    strengths: list[str] = Field(description="Identified strengths in the submission")
    improvements: list[str] = Field(
        description="Constructive improvements for the submission"
    )


class ExplainPathwayChangeArgs(BaseModel):
    old_path_id: str = Field(description="The ID of the previous path")
    new_path_id: str = Field(description="The ID of the new path version")
    changes: list[dict] = Field(
        description="Structured facts detailing what nodes were added or removed"
    )
    proficiency_changes: list[dict] = Field(
        description="Structured facts detailing what skills changed"
    )
