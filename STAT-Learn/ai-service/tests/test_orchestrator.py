import pytest

from app.core.llm import MockChatModel
from app.orchestrator.graph import build_agent_graph


@pytest.mark.asyncio
async def test_orchestrator_direct_response():
    mock_llm = MockChatModel(
        response_content="A generator uses the yield keyword to produce values lazily."
    )
    graph = build_agent_graph(custom_llm=mock_llm)

    state = {
        "messages": [],
        "persona": "tutor",
        "user_message": "What is a generator?",
        "learner_id": "l_test_01",
        "node_id": "n_py_01",
        "conversation_id": None,
        "role_id": None,
        "project_id": None,
        "tool_calls_executed": [],
        "final_response": None,
        "structured_data": None,
        "loop_count": 0,
    }
    result = await graph.ainvoke(state)

    assert (
        result["final_response"]
        == "A generator uses the yield keyword to produce values lazily."
    )
    assert len(result["tool_calls_executed"]) == 0
    assert result["structured_data"] is not None
    assert result["structured_data"]["concept_focus"] == "Core Module Concepts"


@pytest.mark.asyncio
async def test_orchestrator_with_tool_call_loop():
    mock_tool_call = [
        {
            "name": "calculate_skill_gaps",
            "args": {"learner_id": "l_test_01", "role_id": "role_de_01"},
            "id": "call_gaps_1",
        }
    ]
    mock_llm = MockChatModel(
        response_content="Your primary skill gaps are Distributed Systems and Data Modeling.",
        tool_calls_sequence=[mock_tool_call],
    )
    graph = build_agent_graph(custom_llm=mock_llm)

    state = {
        "messages": [],
        "persona": "pathway_reasoner",
        "user_message": "Why do I need Distributed Systems?",
        "learner_id": "l_test_01",
        "node_id": None,
        "conversation_id": None,
        "role_id": "role_de_01",
        "project_id": None,
        "tool_calls_executed": [],
        "final_response": None,
        "structured_data": None,
        "loop_count": 0,
    }
    result = await graph.ainvoke(state)

    assert len(result["tool_calls_executed"]) == 1
    assert result["tool_calls_executed"][0]["tool"] == "calculate_skill_gaps"
    assert "Distributed Systems" in result["final_response"]
    assert result["structured_data"]["target_role"] == "role_de_01"


@pytest.mark.asyncio
async def test_orchestrator_project_mentor_evaluation():
    mock_tool_call = [
        {
            "name": "update_skill_evidence",
            "args": {
                "learner_id": "l_test_01",
                "skill_id": "skill_py",
                "score": 0.9,
                "source_type": "PRACTICAL",
            },
            "id": "call_ev_1",
        }
    ]
    mock_llm = MockChatModel(
        response_content="Excellent implementation of the custom iterator. Passed all test assertions.",
        tool_calls_sequence=[mock_tool_call],
    )
    graph = build_agent_graph(custom_llm=mock_llm)

    state = {
        "messages": [],
        "persona": "project_mentor",
        "user_message": "Submitted my custom iterator for review.",
        "learner_id": "l_test_01",
        "node_id": None,
        "conversation_id": None,
        "role_id": None,
        "project_id": "proj_etl_01",
        "tool_calls_executed": [],
        "final_response": None,
        "structured_data": None,
        "loop_count": 0,
    }
    result = await graph.ainvoke(state)

    assert len(result["tool_calls_executed"]) == 1
    assert result["tool_calls_executed"][0]["tool"] == "update_skill_evidence"
    assert result["structured_data"]["passed"] is True
    assert result["structured_data"]["score"] >= 0.8
