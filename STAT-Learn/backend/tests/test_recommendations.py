"""Deterministic recommendation ranking. Scoring is not invoked."""

import inspect

from fastapi.testclient import TestClient

from app.data.catalogue_seed import PROGRAMMES, Prerequisite, Programme, ProgrammeCompetency
from app.data.diagnostic_seed import DEMO_LEARNER_HEADER, DEMO_LEARNER_TOKEN
from app.main import app
from app.services import recommendation_engine
from app.services.recommendation_engine import (
    MEETS_TARGET_MESSAGE,
    NO_ASSESSMENT_MESSAGE,
    build_pathway,
    rank_programmes,
)

client = TestClient(app)
HEADER = {DEMO_LEARNER_HEADER: DEMO_LEARNER_TOKEN}


def _gap(cid, name, status, gap, current, target="L4", priority=None):
    if priority is None:
        priority = "High" if status == "Priority Gap" else "Medium"
    return {
        "competency_id": cid,
        "name": name,
        "domain": "STAT",
        "status": status,
        "priority": priority,
        "gap": gap,
        "current_level": f"L{current}",
        "current_level_value": current,
        "target_level": target,
        "target_level_value": int(target[1]),
    }


def _programme(pid, title, competency_id, level, prereq_level=None, source="iGOT"):
    return Programme(
        id=pid,
        title=title,
        source=source,
        description="Fixture",
        competencies=(ProgrammeCompetency(competency_id, competency_id, "STAT"),),
        programme_level=level,
        duration_hours=1,
        format="Self-paced module",
        prerequisite=None if prereq_level is None else Prerequisite(competency_id, prereq_level),
    )


def test_gap_programme_is_eligible_and_unrelated_is_not():
    gaps = [_gap("stat-data-analysis", "Statistical Data Analysis", "Priority Gap", 2, 2)]
    programmes = [
        _programme("match", "Analysis", "stat-data-analysis", 3, 2),
        _programme("other", "Sampling", "stat-sampling", 4, 3),
    ]
    result = rank_programmes(gaps, programmes)
    ids = [row["programme_id"] for row in result["recommendations"]]
    assert ids == ["match"]


def test_larger_gap_and_priority_order():
    gaps = [
        _gap("moderate", "Survey Methodology", "Moderate Gap", 1, 2, "L3"),
        _gap("large", "Statistical Data Analysis", "Priority Gap", 2, 2),
    ]
    programmes = [
        _programme("mod", "Survey methodology practicum", "moderate", 3, 2, "NSSTA"),
        _programme("pri", "Analysis of official statistical datasets", "large", 3, 2),
    ]
    result = rank_programmes(gaps, programmes)
    assert [row["programme_id"] for row in result["recommendations"]] == ["pri", "mod"]


def test_appropriate_level_ranks_above_distant_level():
    gaps = [_gap("stat-data-analysis", "Statistical Data Analysis", "Priority Gap", 2, 2)]
    programmes = [
        _programme("advanced", "Advanced interpretation of official releases", "stat-data-analysis", 4, 3),
        _programme("next", "Analysis of official statistical datasets", "stat-data-analysis", 3, 2),
    ]
    result = rank_programmes(gaps, programmes)
    assert [row["programme_id"] for row in result["recommendations"]] == ["next", "advanced"]
    assert result["recommendations"][0]["prerequisite_status"] == "Met"
    assert result["recommendations"][1]["prerequisite_status"] == "Not met"


def test_programme_at_or_below_current_level_is_excluded():
    gaps = [_gap("stat-data-analysis", "Statistical Data Analysis", "Priority Gap", 2, 2)]
    programmes = [
        _programme("low", "Refresher", "stat-data-analysis", 1),
        _programme("same", "Same level", "stat-data-analysis", 2),
        _programme("next", "Next", "stat-data-analysis", 3, 2),
    ]
    result = rank_programmes(gaps, programmes)
    assert [row["programme_id"] for row in result["recommendations"]] == ["next"]


def test_meets_target_is_not_recommended():
    gaps = [_gap("done", "Data Quality", "Meets Target", 0, 4, "L4", "Low")]
    programmes = [_programme("extra", "Extra", "done", 5, 4)]
    result = rank_programmes(gaps, programmes)
    assert result["recommendations"] == []
    assert result["message"] == MEETS_TARGET_MESSAGE


def test_empty_gap_list_has_no_message_from_ranker():
    assert rank_programmes([])["recommendations"] == []


def test_explanation_quotes_the_gap():
    gaps = [_gap("stat-data-analysis", "Statistical Data Analysis", "Priority Gap", 2, 2)]
    result = rank_programmes(gaps, [_programme("next", "Analysis", "stat-data-analysis", 3, 2)])
    reason = result["recommendations"][0]["recommendation_reason"]
    assert "Statistical Data Analysis" in reason
    assert "L2" in reason
    assert "L4" in reason
    assert result["recommendations"][0]["gap"] == 2


def test_tie_break_is_stable():
    gaps = [
        _gap("a-comp", "Alpha", "Moderate Gap", 1, 2, "L3"),
        _gap("b-comp", "Beta", "Moderate Gap", 1, 2, "L3"),
    ]
    first = [_programme("b", "Beta programme", "b-comp", 3, 2), _programme("a", "Alpha programme", "a-comp", 3, 2)]
    second = list(reversed(first))
    assert [row["programme_id"] for row in rank_programmes(gaps, first)["recommendations"]] == [
        row["programme_id"] for row in rank_programmes(gaps, second)["recommendations"]
    ]


def test_unmatched_gap_is_reported():
    gaps = [_gap("missing", "Missing", "Priority Gap", 2, 2)]
    result = rank_programmes(gaps, [])
    assert result["unmatched_gaps"][0]["competency_id"] == "missing"


def test_pathway_puts_met_prerequisite_before_later_programme():
    gaps = [_gap("stat-data-analysis", "Statistical Data Analysis", "Priority Gap", 2, 2)]
    programmes = [
        _programme("advanced", "Advanced", "stat-data-analysis", 4, 3),
        _programme("next", "Next", "stat-data-analysis", 3, 2),
    ]
    ranked = rank_programmes(gaps, programmes)
    steps = build_pathway(ranked)["journeys"][0]["steps"]
    titles = [step["label"] for step in steps if step["state"] in {"Recommended", "Next"} and "programme_id" in step]
    assert titles == ["Next", "Advanced"]
    assert steps[-1]["state"] == "Target"
    assert all(step.get("detail") != "Completed" for step in steps)


def test_seed_order_for_screening_gaps():
    gaps = [
        _gap("stat-data-analysis", "Statistical Data Analysis", "Priority Gap", 2, 2),
        _gap("stat-survey-methodology", "Survey Methodology", "Moderate Gap", 1, 2, "L3"),
        _gap("stat-data-quality", "Data Quality", "Moderate Gap", 1, 3, "L4"),
    ]
    ids = [row["programme_id"] for row in rank_programmes(gaps, list(PROGRAMMES))["recommendations"]]
    assert ids[:4] == [
        "igot-official-analysis",
        "igot-advanced-analysis",
        "nssta-survey-practicum",
        "tpac-data-quality",
    ]


def test_engine_does_not_score_or_call_a_model():
    source = inspect.getsource(recommendation_engine)
    assert "score_attempt" not in source
    assert "llm" not in source.lower()


def test_recommendations_endpoint_uses_session_learner(monkeypatch):
    created = client.post("/assessments/attempts", headers=HEADER)
    attempt_id = created.json()["attempt_id"]
    from app.data.diagnostic_seed import QUESTIONS, SCREENING_ANSWER_INDEX

    for question in QUESTIONS:
        index = SCREENING_ANSWER_INDEX.get(question.id, 0)
        client.post(
            f"/assessments/attempts/{attempt_id}/answers",
            headers=HEADER,
            json={"question_id": question.id, "selected_answer": question.options[index]},
        )
    assert client.post(f"/assessments/attempts/{attempt_id}/complete", headers=HEADER).status_code == 200

    def explode(*_args, **_kwargs):
        raise AssertionError("score recomputed")

    monkeypatch.setattr("app.services.competency_engine.score_attempt", explode)
    denied = client.get("/competencies/recommendations")
    assert denied.status_code == 401
    res = client.get("/competencies/recommendations?learner_id=someone-else", headers=HEADER)
    assert res.status_code == 200
    body = res.json()
    assert body["learner_id"] == "learner_arun_kumar"
    assert body["recommendations"][0]["programme_id"] == "igot-official-analysis"
    assert "L2" in body["recommendations"][0]["recommendation_reason"]
    empty = client.get("/competencies/recommendations", headers={DEMO_LEARNER_HEADER: "nope"})
    assert empty.status_code == 401


def test_no_attempt_message():
    from app.services.competency_store import reset_memory

    reset_memory()
    res = client.get("/competencies/recommendations", headers=HEADER)
    assert res.status_code == 200
    assert res.json()["message"] == NO_ASSESSMENT_MESSAGE
    assert res.json()["recommendations"] == []
    catalogue = client.get("/competencies/catalogue", headers=HEADER)
    assert catalogue.status_code == 200
    body = catalogue.json()
    assert body["synthetic"] is False
    assert body["programmes"]
    assert body["programmes"][0]["external_url"].startswith("https://portal.igotkarmayogi.gov.in/app/toc/")
