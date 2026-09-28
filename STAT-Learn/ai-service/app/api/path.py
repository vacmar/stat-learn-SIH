from fastapi import APIRouter

from app.models.structured import PathGenerateRequest, PathwayExplanation
from app.services.path_generator import generate_pathway

router = APIRouter(prefix="/path", tags=["Path Generation"])


@router.post("/generate", response_model=PathwayExplanation)
async def generate_learner_path(request: PathGenerateRequest) -> PathwayExplanation:
    """Author a tailored learning pathway (and capstone) from the learner profile."""
    return await generate_pathway(request)
