from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.auth import get_current_learner
from app.models.domain import Learner
from app.services import verification_service

router = APIRouter(prefix="/verification", tags=["Verification"])


class VerificationSubmitPayload(BaseModel):
    assessment: float = Field(ge=0.0, le=1.0)
    practical: float = Field(ge=0.0, le=1.0)
    evidence: float | None = Field(default=None, ge=0.0, le=1.0)
    coursework: float | None = Field(default=None, ge=0.0, le=1.0)


@router.post("/skills/{skill_id}/start")
def start_skill_verification(
    skill_id: str, learner: Learner = Depends(get_current_learner)
):
    try:
        session = verification_service.start_verification(learner.learner_id, skill_id)
        return {"message": "Verification started", "session": session}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/skills/{skill_id}/submit")
def submit_skill_verification(
    skill_id: str,
    payload: VerificationSubmitPayload,
    learner: Learner = Depends(get_current_learner),
):
    try:
        result = verification_service.submit_verification(
            learner.learner_id,
            skill_id,
            assessment=payload.assessment,
            practical=payload.practical,
            evidence=payload.evidence,
            coursework=payload.coursework,
        )
        return {"message": "Verification submitted", "result": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/skills/{skill_id}/result")
def get_skill_verification_result(
    skill_id: str, learner: Learner = Depends(get_current_learner)
):
    try:
        result = verification_service.get_verification_result(
            learner.learner_id, skill_id
        )
        return {"skill_id": skill_id, "result": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
