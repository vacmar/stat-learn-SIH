from app.core.cache import get_redis_client


def invalidate_node_cache(node_id: str, conversation_id: str, assessment_id: str):
    """
    Invalidates conversation and assessment state from Redis.
    Called ONLY AFTER a node completes and state is durably written to DB.
    """
    try:
        cache = get_redis_client()

        # 1. Invalidate Conversation
        if conversation_id:
            cache.delete(f"conversations:{conversation_id}:messages")
            cache.delete(f"conversations:{conversation_id}:summary")

        # 2. Invalidate Active Assessment
        if assessment_id:
            cache.delete(f"assessments:active:{assessment_id}")

    except Exception as e:
        # We don't fail the completion if Redis deletion fails
        import logging

        logging.getLogger(__name__).error(f"Failed to invalidate node cache: {e}")
