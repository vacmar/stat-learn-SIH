import json
import logging
from typing import Any, cast

import redis
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.cache import get_redis_client
from app.repository import state_repo
from app.services.assessment_scoring import score_answers

router = APIRouter(prefix="/assessments", tags=["Assessments"])
logger = logging.getLogger(__name__)


class AnswerPayload(BaseModel):
    question_id: str
    answer: str


@router.post("/start")
def start_assessment(
    assessment_id: str, cache: redis.Redis = Depends(get_redis_client)
):
    key = f"assessments:active:{assessment_id}"
    state = {"status": "started", "answers": []}
    try:
        cache.set(key, json.dumps(state), ex=86400)  # 24h TTL
    except Exception as e:
        logger.error(f"Redis unavailable: {e}")
        # In a strict environment we might fail, but for now we continue
    return {"message": "Assessment started", "assessment_id": assessment_id}


@router.post("/{assessment_id}/answer")
def submit_answer(
    assessment_id: str,
    payload: AnswerPayload,
    cache: redis.Redis = Depends(get_redis_client),
):
    key = f"assessments:active:{assessment_id}"
    try:
        raw_state = cast(str, cache.get(key))
    except Exception as e:
        logger.error(f"Redis unavailable: {e}")
        raw_state = None

    if not raw_state:
        state: dict[str, Any] = {"status": "in_progress", "answers": []}
    else:
        state = json.loads(raw_state)

    state["answers"].append(payload.model_dump())

    try:
        cache.set(key, json.dumps(state), ex=86400)  # Reset 24h TTL
    except Exception:
        pass

    return {"message": "Answer recorded", "assessment_id": assessment_id}


@router.post("/{assessment_id}/finalize")
def finalize_assessment(
    assessment_id: str, cache: redis.Redis = Depends(get_redis_client)
):
    key = f"assessments:active:{assessment_id}"

    # 1. Read from Redis
    try:
        raw_state = cast(str, cache.get(key))
    except Exception:
        raw_state = None

    if raw_state:
        state: dict[str, Any] = json.loads(raw_state)
    else:
        state = {"status": "in_progress", "answers": []}

    score = score_answers(state.get("answers", []))
    result = {
        "status": "completed",
        "score": score,
        "answers": state["answers"],
    }

    # 2. Persist to DB (Durable)
    try:
        state_repo.save_assessment_result(assessment_id, result)
    except Exception:
        raise HTTPException(status_code=500, detail="Database write failed")

    # 3. Delete from Redis
    try:
        cache.delete(key)
    except Exception:
        pass

    return {"message": "Assessment finalized", "result": result}


@router.get("/{assessment_id}/result")
def get_assessment_result(assessment_id: str):
    # Reads should always go to DB for completed assessments
    result = state_repo.get_assessment(assessment_id)
    if not result:
        raise HTTPException(status_code=404, detail="Assessment result not found")
    if isinstance(result, str):
        state_payload = json.loads(result)
    else:
        state_payload = result
    return {
        "message": "Assessment state retrieved",
        "assessment_id": assessment_id,
        "state": state_payload,
    }
