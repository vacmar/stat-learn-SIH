import pytest

from app.tools.registry import ALL_TOOLS, TOOLS_BY_NAME

EXPECTED_TOOLS = [
    "get_learner_profile",
    "get_current_skill_state",
    "get_target_requirements",
    "calculate_skill_gaps",
    "get_prerequisites",
    "find_courses_for_skill",
    "find_projects_for_skills",
    "generate_candidate_paths",
    "rank_candidate_paths",
    "get_learning_node_state",
    "get_conversation_context",
    "get_weak_concepts",
    "record_assessment_result",
    "update_skill_evidence",
    "check_unlock_conditions",
    "complete_learning_node",
]


def test_all_sixteen_tools_registered():
    assert len(ALL_TOOLS) == 20
    assert len(TOOLS_BY_NAME) == 20
    for tool_name in EXPECTED_TOOLS:
        assert tool_name in TOOLS_BY_NAME, f"Tool {tool_name} is missing from registry"


def test_tool_metadata_validity():
    for tool_inst in ALL_TOOLS:
        assert tool_inst.name, "Tool must have a valid name"
        assert tool_inst.description, f"Tool {tool_inst.name} missing description"
        assert tool_inst.args_schema is not None, (
            f"Tool {tool_inst.name} missing args_schema"
        )
        schema_dict = tool_inst.args_schema.model_json_schema()
        assert "properties" in schema_dict


@pytest.mark.asyncio
async def test_tool_invocations():
    # Test read tools
    profile = await TOOLS_BY_NAME["get_learner_profile"].ainvoke(
        {"learner_id": "l_test_01"}
    )
    assert "learner_id" in profile

    gaps = await TOOLS_BY_NAME["calculate_skill_gaps"].ainvoke(
        {"learner_id": "l_test_01", "role_id": "r_de_01"}
    )
    assert isinstance(gaps, list)
    assert len(gaps) > 0

    node_state = await TOOLS_BY_NAME["get_learning_node_state"].ainvoke(
        {"node_id": "node_py_01"}
    )
    assert "status" in node_state

    # Test state transition tool
    completion_res = await TOOLS_BY_NAME["complete_learning_node"].ainvoke(
        {"node_id": "node_py_01", "assessment_score": 0.85, "practical_pass": True}
    )
    assert completion_res.get("success") is True
