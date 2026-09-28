from typing import Any

from pydantic import BaseModel, Field


class TutorResponse(BaseModel):
    """Structured response format for the AI Tutor persona."""

    content: str = Field(
        description="Primary explanation, answer, or conversational instruction"
    )
    concept_focus: str = Field(
        description="Core concept currently being taught or reviewed"
    )
    check_question: str | None = Field(
        default=None, description="Check-for-understanding question for the learner"
    )
    recommended_action: str = Field(
        default="continue_learning",
        description="Recommended next step: continue_learning, practice_exercise, take_assessment, or review_prerequisites",
    )
    remediation_needed: bool = Field(
        default=False,
        description="Flag indicating if the learner requires targeted remediation on a weak concept",
    )
    tools_used: list[str] = Field(
        default_factory=list, description="List of tools invoked during reasoning"
    )


class PathwayStage(BaseModel):
    stage_number: int
    course_name: str
    rationale: str
    target_skills: list[str]


class CapstoneRequirement(BaseModel):
    requirement_id: str
    description: str
    mandatory: bool = True


class CapstoneProject(BaseModel):
    title: str
    description: str
    requirements: list[CapstoneRequirement] = Field(default_factory=list)


class PathwayExplanation(BaseModel):
    """Structured rationale for generated and ranked learning pathways."""

    summary: str = Field(
        description="Executive summary of the candidate path and progression strategy"
    )
    target_role: str = Field(description="The target career role")
    stages: list[PathwayStage] = Field(
        default_factory=list, description="Ordered stages in the pathway with rationale"
    )
    gap_analysis_summary: str = Field(
        description="Explanation of how the path systematically closes identified skill gaps"
    )
    estimated_total_hours: float = Field(
        default=0.0, description="Estimated total hours to complete the path"
    )
    tools_used: list[str] = Field(
        default_factory=list, description="List of tools invoked during reasoning"
    )
    capstone: CapstoneProject | None = Field(
        default=None,
        description="Recommended capstone project tailored to the learner profile",
    )


class PathGenerateRequest(BaseModel):
    """Learner profile payload used to author a tailored pathway."""

    learner_id: str = "learner_default"
    name: str | None = None
    target_role: str = Field(description="Human-readable target role title")
    target_role_id: str | None = None
    custom_role_title: str | None = None
    target_domain: str | None = None
    experience_level: str | None = None
    prior_experience: str | None = None
    known_skills: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    learning_style: str | None = None
    weekly_time: int | None = 10
    goals: list[str] = Field(default_factory=list)


class ProjectMentorFeedback(BaseModel):
    """Structured evaluation and mentorship for project milestones and submissions."""

    project_title: str = Field(
        description="Title of the project or capstone being mentored"
    )
    passed: bool = Field(
        description="Whether the submission meets the milestone passing criteria"
    )
    score: float = Field(description="Score or evaluation metric (0.0 to 1.0)")
    strengths: list[str] = Field(
        default_factory=list,
        description="Key strengths demonstrated in the implementation",
    )
    areas_for_improvement: list[str] = Field(
        default_factory=list, description="Specific, actionable areas to improve"
    )
    next_milestone: str | None = Field(
        default=None, description="Recommended next task or project stage"
    )
    tools_used: list[str] = Field(
        default_factory=list, description="List of tools invoked during reasoning"
    )


class ChatRequest(BaseModel):
    message: str = Field(description="User prompt or question")
    learner_id: str = Field(
        default="learner_default_01", description="Unique learner identifier"
    )
    node_id: str | None = Field(
        default=None,
        description="Path node identifier (if learning inside a node workspace)",
    )
    conversation_id: str | None = Field(
        default=None, description="Active conversation session ID"
    )
    role_id: str | None = Field(
        default=None, description="Career role ID (for pathway reasoning)"
    )
    project_id: str | None = Field(
        default=None, description="Project ID (for project mentor)"
    )
    history: list[dict[str, str]] = Field(
        default_factory=list,
        description="Prior chat turns [{role, content}] for conversational continuity",
    )
    lesson_context: dict[str, Any] | None = Field(
        default=None,
        description="Current/upcoming node titles and goal for scoped tutoring",
    )
    lesson_title: str | None = Field(
        default=None, description="Human title of the active learning node"
    )
    upcoming_nodes: list[str] = Field(
        default_factory=list,
        description="Titles of later path nodes (defer questions about these)",
    )
    previous_nodes: list[str] = Field(
        default_factory=list,
        description="Titles of earlier completed/prior path nodes",
    )


class ChatResponse(BaseModel):
    message: str = Field(description="Primary text response returned to the learner")
    persona: str = Field(
        description="Active persona: tutor, pathway_reasoner, or project_mentor"
    )
    structured: dict[str, Any] | None = Field(
        default=None, description="Parsed structured data schema"
    )
    tool_calls: list[dict[str, Any]] = Field(
        default_factory=list, description="Record of tools called and executed"
    )
