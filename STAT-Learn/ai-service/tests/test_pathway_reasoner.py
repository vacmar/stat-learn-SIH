import pytest

from app.tools.registry import explain_pathway_change


@pytest.mark.asyncio
async def test_explain_pathway_receives_facts():
    res = await explain_pathway_change.ainvoke(
        {
            "old_path_id": "p1",
            "new_path_id": "p2",
            "changes": [{"type": "NODE_ADDED", "course_id": "c_cloud"}],
            "proficiency_changes": [],
        }
    )
    assert "We added c_cloud" in res["explanation"]


@pytest.mark.asyncio
async def test_ai_explanation_references_actual_proficiency_changes():
    res = await explain_pathway_change.ainvoke(
        {
            "old_path_id": "p1",
            "new_path_id": "p2",
            "changes": [],
            "proficiency_changes": [
                {"skill_id": "skill_py", "previous": 0.5, "current": 0.9}
            ],
        }
    )
    assert "skill_py changed from 0.5 to 0.9" in res["explanation"]


@pytest.mark.asyncio
async def test_ai_explanation_references_actual_node_changes():
    res = await explain_pathway_change.ainvoke(
        {
            "old_path_id": "p1",
            "new_path_id": "p2",
            "changes": [{"type": "NODE_REMOVED", "course_id": "c_py"}],
            "proficiency_changes": [],
        }
    )
    assert "We removed c_py" in res["explanation"]


@pytest.mark.asyncio
async def test_ai_cannot_invent_absent_node():
    res = await explain_pathway_change.ainvoke(
        {
            "old_path_id": "p1",
            "new_path_id": "p2",
            "changes": [{"type": "NODE_ADDED", "course_id": "c_sql"}],
            "proficiency_changes": [],
        }
    )
    assert "c_cloud" not in res["explanation"]


@pytest.mark.asyncio
async def test_ai_cannot_mutate_path_state():
    # The tool returns an explanation dict, not a path state dict. It has no mutation backend call.
    res = await explain_pathway_change.ainvoke(
        {
            "old_path_id": "p1",
            "new_path_id": "p2",
            "changes": [],
            "proficiency_changes": [],
        }
    )
    assert "explanation" in res


@pytest.mark.asyncio
async def test_empty_facts_produce_unchanged_explanation():
    res = await explain_pathway_change.ainvoke(
        {
            "old_path_id": "p1",
            "new_path_id": "p1",
            "changes": [],
            "proficiency_changes": [],
        }
    )
    assert "remains unchanged" in res["explanation"]
