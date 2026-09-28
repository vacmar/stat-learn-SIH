import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.tools.backend_client import BackendClient
from app.tools.registry import get_lesson_context, record_mistake

client = TestClient(app)


@pytest.mark.asyncio
async def test_tutor_tools_direct_invocation():
    with patch.object(BackendClient, "_safe_get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {"lesson": "Test context"}
        res = await get_lesson_context.ainvoke({"node_id": "n1"})
        assert res["lesson"] == "Test context"

    with patch(
        "app.tools.registry.backend_client.record_mistake", new_callable=AsyncMock
    ) as mock_rm:
        mock_rm.return_value = {"status": "recorded"}
        res2 = await record_mistake.ainvoke(
            {"learner_id": "L1", "node_id": "n1", "concept": "X", "description": "Y"}
        )
        assert res2["status"] == "recorded"
        mock_rm.assert_awaited()


async def mock_astream_events_normal(*args, **kwargs):
    chunk1 = MagicMock()
    chunk1.content = "Hello "
    yield {
        "event": "on_chat_model_stream",
        "name": "agent_node",
        "data": {"chunk": chunk1},
    }

    chunk2 = MagicMock()
    chunk2.content = "world."
    yield {
        "event": "on_chat_model_stream",
        "name": "agent_node",
        "data": {"chunk": chunk2},
    }

    yield {
        "event": "on_chain_end",
        "name": "validator_node",
        "data": {
            "output": {"structured_data": {"concept_focus": "Intro", "tools_used": []}}
        },
    }


@patch(
    "app.api.chat.orchestrator_graph.astream_events",
    side_effect=mock_astream_events_normal,
)
def test_streaming_events(mock_stream):
    req = {"message": "Hello tutor", "learner_id": "L1", "node_id": "n1"}

    events = []
    with client.stream("POST", "/chat/tutor/stream", json=req) as response:
        for line in response.iter_lines():
            if line:
                events.append(line)

    token_events = [e for e in events if e.startswith("event: token")]
    assert len(token_events) == 2

    metadata_events = [e for e in events if e.startswith("event: metadata")]
    assert len(metadata_events) == 1

    meta_idx = events.index(metadata_events[0])
    data_line = events[meta_idx + 1]
    meta_json = json.loads(data_line[6:])
    assert "concept_focus" in meta_json

    done_events = [e for e in events if e.startswith("event: done")]
    assert len(done_events) == 1


async def mock_astream_events_tool(*args, **kwargs):
    # Simulate a tool call where chunk content might be empty or a list
    chunk1 = MagicMock()
    chunk1.content = ""  # Langchain empty content for tool call
    yield {
        "event": "on_chat_model_stream",
        "name": "agent_node",
        "data": {"chunk": chunk1},
    }

    yield {
        "event": "on_chain_end",
        "name": "validator_node",
        "data": {
            "output": {
                "structured_data": {
                    "concept_focus": "Tools",
                    "tools_used": ["record_mistake"],
                }
            }
        },
    }


@patch(
    "app.api.chat.orchestrator_graph.astream_events",
    side_effect=mock_astream_events_tool,
)
def test_tool_call_during_streaming(mock_stream):
    req = {"message": "Help", "learner_id": "L1", "node_id": "n1"}

    events = []
    with client.stream("POST", "/chat/tutor/stream", json=req) as response:
        for line in response.iter_lines():
            if line:
                events.append(line)

    # No tokens should have been emitted because content was empty
    token_events = [e for e in events if e.startswith("event: token")]
    assert len(token_events) == 0

    metadata_events = [e for e in events if e.startswith("event: metadata")]
    meta_idx = events.index(metadata_events[0])
    meta_json = json.loads(events[meta_idx + 1][6:])
    assert "record_mistake" in meta_json["tools_used"]
