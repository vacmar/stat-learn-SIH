import json
import operator
import re
from typing import Annotated, Any, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langgraph.graph import END, StateGraph

from app.context.builder import context_builder
from app.core.llm import get_llm
from app.models.structured import (
    PathwayExplanation,
    PathwayStage,
    ProjectMentorFeedback,
    TutorResponse,
)
from app.tools.registry import ALL_TOOLS, TOOLS_BY_NAME


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    persona: str
    user_message: str
    learner_id: str
    node_id: str | None
    conversation_id: str | None
    role_id: str | None
    project_id: str | None
    tool_calls_executed: Annotated[list[dict[str, Any]], operator.add]
    final_response: str | None
    structured_data: dict[str, Any] | None
    loop_count: int


def _extract_json(text: str) -> dict[str, Any] | None:
    """Attempt to extract JSON from raw text or markdown codeblocks."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass
    # Check for ```json ... ``` blocks
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except (json.JSONDecodeError, TypeError):
            pass
    return None


async def context_node(state: AgentState) -> dict[str, Any]:
    """Gather background state and prepare messages with system prompt."""
    if state.get("messages"):
        # If messages already built, proceed
        return {"loop_count": 0}

    built_messages = await context_builder.build_messages(
        persona=state.get("persona", "tutor"),
        user_message=state.get("user_message", ""),
        learner_id=state.get("learner_id", "learner_01"),
        node_id=state.get("node_id"),
        conversation_id=state.get("conversation_id"),
        role_id=state.get("role_id"),
    )
    return {"messages": built_messages, "loop_count": 0}


async def agent_node(state: AgentState, llm=None) -> dict[str, Any]:
    """Execute LLM with bound tools."""
    active_llm = llm or get_llm()
    llm_with_tools = active_llm.bind_tools(ALL_TOOLS)
    response = await llm_with_tools.ainvoke(state["messages"])
    current_loops = state.get("loop_count", 0) + 1
    return {"messages": [response], "loop_count": current_loops}


def router_edge(state: AgentState) -> str:
    """Route to tools_node if tool calls exist, else to validator_node (or break loops)."""
    # Guard against infinite agent loops
    if state.get("loop_count", 0) >= 5:
        return "validator_node"

    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and getattr(
        last_message, "tool_calls", None
    ):
        return "tools_node"
    return "validator_node"


async def tools_node(state: AgentState) -> dict[str, Any]:
    """Execute all requested tool calls asynchronously."""
    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, "tool_calls", []) or []

    tool_messages: list[BaseMessage] = []
    executed_records: list[dict[str, Any]] = []

    for tc in tool_calls:
        name = tc["name"]
        args = tc.get("args", {})
        call_id = tc.get("id", f"call_{name}")

        tool_inst = TOOLS_BY_NAME.get(name)
        if tool_inst:
            try:
                result = await tool_inst.ainvoke(args)
            except Exception as e:
                result = {"error": f"Tool execution failed: {e!s}"}
        else:
            result = {"error": f"Tool {name} not found"}

        tool_messages.append(
            ToolMessage(content=json.dumps(result), tool_call_id=call_id)
        )
        executed_records.append({"tool": name, "args": args, "result": result})

    return {"messages": tool_messages, "tool_calls_executed": executed_records}


async def validator_node(state: AgentState) -> dict[str, Any]:
    """Parse and normalize final output into structured Pydantic schemas."""
    last_message = state["messages"][-1]
    content = (
        str(last_message.content) if last_message.content else "Response generated."
    )
    persona = state.get("persona", "tutor")
    tools_used = [t["tool"] for t in state.get("tool_calls_executed", [])]

    parsed_json = _extract_json(content) or {}
    structured_data: dict[str, Any] = {}

    if persona == "pathway_reasoner":
        stages_raw = parsed_json.get("stages", [])
        stages = [
            PathwayStage(**s)
            if isinstance(s, dict)
            else PathwayStage(
                stage_number=i + 1,
                course_name=str(s),
                rationale="Curriculum progression",
                target_skills=[],
            )
            for i, s in enumerate(stages_raw)
        ]
        structured_pathway = PathwayExplanation(
            summary=parsed_json.get("summary", content),
            target_role=parsed_json.get(
                "target_role", state.get("role_id") or "Target Role"
            ),
            stages=stages,
            gap_analysis_summary=parsed_json.get(
                "gap_analysis_summary",
                "Curriculum closes prerequisites and skill gaps.",
            ),
            estimated_total_hours=float(parsed_json.get("estimated_total_hours", 40.0)),
            tools_used=tools_used,
        )
        structured_data = structured_pathway.model_dump()
        final_text = structured_pathway.summary

    elif persona == "project_mentor":
        structured_project = ProjectMentorFeedback(
            project_title=parsed_json.get(
                "project_title", state.get("project_id") or "Practical Capstone"
            ),
            passed=bool(parsed_json.get("passed", True)),
            score=float(parsed_json.get("score", 0.85)),
            strengths=parsed_json.get(
                "strengths",
                [
                    "Clear functional separation",
                    "Effective prerequisite concept application",
                ],
            ),
            areas_for_improvement=parsed_json.get(
                "areas_for_improvement", ["Add error handling for edge cases"]
            ),
            next_milestone=parsed_json.get(
                "next_milestone", "Proceed to integration testing"
            ),
            tools_used=tools_used,
        )
        structured_data = structured_project.model_dump()
        final_text = content

    else:  # tutor
        structured_tutor = TutorResponse(
            content=parsed_json.get("content", content),
            concept_focus=parsed_json.get("concept_focus", "Core Module Concepts"),
            check_question=parsed_json.get(
                "check_question",
                "Would you like to try a code exercise to verify this?",
            ),
            recommended_action=parsed_json.get(
                "recommended_action", "practice_exercise"
            ),
            remediation_needed=bool(parsed_json.get("remediation_needed", False)),
            tools_used=tools_used,
        )
        structured_data = structured_tutor.model_dump()
        final_text = structured_tutor.content

    return {
        "final_response": final_text,
        "structured_data": structured_data,
    }


def build_agent_graph(custom_llm=None):
    """Build and compile the orchestrator StateGraph."""
    graph_builder = StateGraph(AgentState)

    async def run_agent_node(s: AgentState) -> dict[str, Any]:
        return await agent_node(s, llm=custom_llm)

    graph_builder.add_node("context_node", context_node)
    graph_builder.add_node("agent_node", run_agent_node)
    graph_builder.add_node("tools_node", tools_node)
    graph_builder.add_node("validator_node", validator_node)

    graph_builder.set_entry_point("context_node")
    graph_builder.add_edge("context_node", "agent_node")
    graph_builder.add_conditional_edges(
        "agent_node",
        router_edge,
        {"tools_node": "tools_node", "validator_node": "validator_node"},
    )
    graph_builder.add_edge("tools_node", "agent_node")
    graph_builder.add_edge("validator_node", END)

    return graph_builder.compile()


# Default compiled graph
orchestrator_graph = build_agent_graph()
