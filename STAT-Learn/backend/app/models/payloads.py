from pydantic import BaseModel


class CompletionRequest(BaseModel):
    learner_id: str
    assessment_score: float
    practical_pass: bool
