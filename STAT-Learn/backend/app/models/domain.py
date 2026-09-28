from enum import Enum

from pydantic import BaseModel


class NodeStatus(str, Enum):
    LOCKED = "LOCKED"
    UNLOCKED = "UNLOCKED"
    IN_PROGRESS = "IN_PROGRESS"
    ASSESSMENT_READY = "ASSESSMENT_READY"
    REMEDIATION = "REMEDIATION"
    COMPLETED = "COMPLETED"
    REVIEW = "REVIEW"


class Account(BaseModel):
    account_id: str
    email: str
    password_hash: str
    created_at: str
    updated_at: str
    is_active: bool = True


class Learner(BaseModel):
    learner_id: str
    account_id: str
    name: str
    email: str | None = None
    target_role_id: str | None = None
    posting: str | None = None
    ministry: str | None = None
    state_name: str | None = None
    department: str | None = None
    organisation: str | None = None
    designation: str | None = None
    target_domain: str | None = None
    goals: list[str] = []
    experience_level: str | None = None
    prior_experience: str | None = None
    education: str | None = None
    known_skills: list[str] = []
    self_reported_proficiency: dict[str, float] = {}
    interests: list[str] = []
    learning_style: str | None = None
    weekly_time: int | None = None
    onboarding_completed: bool = False
    onboarding_version: int = 1
    onboarding_completed_at: str | None = None
    created_at: str
    updated_at: str


class Skill(BaseModel):
    skill_id: str
    name: str


class PathNode(BaseModel):
    node_id: str
    path_id: str
    course_id: str
    sequence_order: int
    status: NodeStatus = NodeStatus.LOCKED


class LearningPath(BaseModel):
    path_id: str
    learner_id: str
    version: int
    previous_path_id: str | None = None
    created_at: str
    is_active: bool
