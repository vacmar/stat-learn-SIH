import pytest
from langchain_core.messages import HumanMessage, SystemMessage

from app.context.builder import ContextBuilder


@pytest.mark.asyncio
async def test_context_builder_tutor_persona():
    builder = ContextBuilder()
    messages = await builder.build_messages(
        persona="tutor",
        user_message="How do decorators work in Python?",
        learner_id="l_test_01",
        node_id="node_py_01",
    )
    assert len(messages) >= 2
    assert isinstance(messages[0], SystemMessage)
    assert isinstance(messages[-1], HumanMessage)
    assert "manthaino Adaptive AI Tutor" in messages[0].content
    assert "node_py_01" in messages[0].content or "Python" in messages[0].content
    assert messages[-1].content == "How do decorators work in Python?"


@pytest.mark.asyncio
async def test_context_builder_pathway_reasoner():
    builder = ContextBuilder()
    messages = await builder.build_messages(
        persona="pathway_reasoner",
        user_message="Why does Data Modeling come after SQL?",
        role_id="role_de_01",
    )
    assert "Pathway Reasoning Engine" in messages[0].content
    assert "Target Career Role: role_de_01" in messages[0].content


@pytest.mark.asyncio
async def test_context_builder_with_history():
    builder = ContextBuilder()
    history = [
        {"role": "user", "content": "What is a closure?"},
        {
            "role": "assistant",
            "content": "A closure is a nested function that remembers enclosing scope values.",
        },
    ]
    messages = await builder.build_messages(
        persona="tutor",
        user_message="Can you give an example?",
        history=history,
    )
    assert len(messages) == 4
    assert messages[1].content == "What is a closure?"
    assert (
        messages[2].content
        == "A closure is a nested function that remembers enclosing scope values."
    )
    assert messages[3].content == "Can you give an example?"
