import json
import logging
from typing import Any, cast

import redis
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from app.core.cache import get_redis_client
from app.repository import state_repo

router = APIRouter(prefix="/conversations", tags=["Conversations"])


class MessagePayload(BaseModel):
    role: str
    content: str


logger = logging.getLogger(__name__)


@router.get("/{conversation_id}")
def get_conversation(
    conversation_id: str,
    limit: int = 10,
    cache: redis.Redis = Depends(get_redis_client),
):
    key = f"conversations:{conversation_id}:messages"

    try:
        raw_messages = cast(list[Any], cache.lrange(key, -limit, -1))
    except Exception as e:
        logger.error(f"Redis unavailable: {e}")
        raw_messages = []

    messages = []
    if raw_messages:
        for rm in raw_messages:
            try:
                messages.append(json.loads(rm))
            except json.JSONDecodeError:
                pass
    else:
        messages = state_repo.get_conversation(conversation_id)
        if messages:
            try:
                for m in messages:
                    cache.rpush(key, json.dumps(m))
                cache.expire(key, 3600)
            except Exception as e:
                logger.error(f"Failed to populate Redis cache: {e}")

    messages = messages[-limit:]

    try:
        summary = cast(str, cache.get(f"conversations:{conversation_id}:summary"))
        if not summary:
            summary = state_repo.get_conversation_summary(conversation_id)
            cache.set(f"conversations:{conversation_id}:summary", summary, ex=3600)
    except Exception:
        summary = state_repo.get_conversation_summary(conversation_id)

    return {
        "conversation_id": conversation_id,
        "summary": summary,
        "recent_messages": messages,
    }


def generate_rolling_summary(conversation_id: str):
    """Background task to generate a new summary based on history."""
    messages = state_repo.get_conversation(conversation_id)
    old_summary = state_repo.get_conversation_summary(conversation_id)

    # Mock summarization logic (in production, call LLM)
    new_summary = (
        f"{old_summary} | Summarized {len(messages)} messages at {len(messages)}."
    )

    # Persist and update cache
    state_repo.save_conversation_summary(conversation_id, new_summary)
    try:
        cache = get_redis_client()
        cache.set(f"conversations:{conversation_id}:summary", new_summary, ex=3600)
    except Exception:
        pass


@router.post("/{conversation_id}/messages")
def add_message(
    conversation_id: str,
    payload: MessagePayload,
    background_tasks: BackgroundTasks,
    cache: redis.Redis = Depends(get_redis_client),
):
    key = f"conversations:{conversation_id}:messages"
    msg_dict = payload.model_dump()

    # 1. DB First (Durable Write)
    try:
        state_repo.save_conversation_message(conversation_id, msg_dict)
    except Exception:
        raise HTTPException(status_code=500, detail="Database write failed")

    # 2. Redis Update (Ephemeral)
    try:
        message_str = json.dumps(msg_dict)
        cache.rpush(key, message_str)
        cache.expire(key, 3600)
    except Exception as e:
        logger.error(f"Failed to update Redis cache: {e}")

    # 3. Rolling Summary check
    try:
        msg_count = len(state_repo.get_conversation(conversation_id))
        if msg_count > 0 and msg_count % 5 == 0:
            background_tasks.add_task(generate_rolling_summary, conversation_id)
    except Exception as e:
        logger.error(f"Failed to trigger summarization: {e}")

    return {"status": "success", "conversation_id": conversation_id}
