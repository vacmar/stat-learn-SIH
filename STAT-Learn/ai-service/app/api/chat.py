import json
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.structured import ChatRequest, ChatResponse
from app.orchestrator.graph import orchestrator_graph
from app.services.lesson_chat import run_lesson_chat

router = APIRouter(prefix="/chat", tags=["Chat & Personas"])


async def _run_persona(request: ChatRequest, persona: str) -> ChatResponse:
    try:
        init_state: dict[str, Any] = {
            "messages": [],
            "persona": persona,
            "user_message": request.message,
            "learner_id": request.learner_id,
            "node_id": request.node_id,
            "conversation_id": request.conversation_id,
            "role_id": request.role_id,
            "project_id": request.project_id,
            "tool_calls_executed": [],
            "final_response": None,
            "structured_data": None,
            "loop_count": 0,
        }
        result = await orchestrator_graph.ainvoke(init_state)
        return ChatResponse(
            message=result.get("final_response") or "Response generated.",
            persona=persona,
            structured=result.get("structured_data"),
            tool_calls=result.get("tool_calls_executed", []),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Agent orchestration failed: {e!s}"
        )


async def _stream_persona(request: ChatRequest, persona: str):
    init_state: dict[str, Any] = {
        "messages": [],
        "persona": persona,
        "user_message": request.message,
        "learner_id": request.learner_id,
        "node_id": request.node_id,
        "conversation_id": request.conversation_id,
        "role_id": request.role_id,
        "project_id": request.project_id,
        "tool_calls_executed": [],
        "final_response": None,
        "structured_data": None,
        "loop_count": 0,
    }

    try:
        async for event in orchestrator_graph.astream_events(init_state, version="v1"):
            kind = event["event"]
            name = event.get("name", "")

            # Stream tokens
            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if getattr(chunk, "content", None):
                    content = chunk.content
                    if isinstance(content, str) and content:
                        # Yield SSE token
                        clean_text = content.replace(
                            "\n", "\\n"
                        )  # basic escaping for SSE data single line if needed, but SSE supports multiline if we prefix `data: `
                        # Actually standard SSE handles multiline by repeating `data: `
                        lines = content.split("\n")
                        sse_data = "\n".join([f"data: {line}" for line in lines])
                        yield f"event: token\n{sse_data}\n\n"

            # Stream final metadata when validator completes
            elif kind == "on_chain_end" and name == "validator_node":
                output = event["data"].get("output", {})
                structured = output.get("structured_data")
                if structured:
                    meta_json = json.dumps(structured)
                    yield f"event: metadata\ndata: {meta_json}\n\n"

        # Signal completion
        yield "event: done\ndata: {}\n\n"
    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'detail': str(e)})}\n\n"


@router.post("/tutor/stream")
async def stream_tutor(request: ChatRequest):
    """Invoke the Adaptive AI Tutor with SSE streaming."""
    return StreamingResponse(
        _stream_persona(request, "tutor"), media_type="text/event-stream"
    )


@router.post("/tutor", response_model=ChatResponse)
async def chat_tutor(request: ChatRequest) -> ChatResponse:
    """Invoke the Adaptive AI Tutor persona for learning workspace dialogues."""
    return await _run_persona(request, "tutor")


@router.post("/lesson", response_model=ChatResponse)
async def chat_lesson(request: ChatRequest) -> ChatResponse:
    """Interactive ChatGPT-style lesson chat scoped to the active path node."""
    try:
        return await run_lesson_chat(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lesson chat failed: {e!s}")


@router.post("/pathway-explanation", response_model=ChatResponse)
async def chat_pathway(request: ChatRequest) -> ChatResponse:
    """Invoke the Pathway Reasoner to explain course orderings, prerequisites, and gap reductions."""
    return await _run_persona(request, "pathway_reasoner")


@router.post("/project-mentor", response_model=ChatResponse)
async def chat_mentor(request: ChatRequest) -> ChatResponse:
    """Invoke the Project Mentor to review milestones, evaluate code, and submit skill evidence."""
    return await _run_persona(request, "project_mentor")
