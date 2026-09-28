"""Deterministic catalogue ranking. Does not score competencies."""

from __future__ import annotations

from datetime import UTC, datetime

from app.data.catalogue_seed import PROGRAMMES, Programme
from app.services.igot_catalogue import catalogue_rows

NO_ASSESSMENT_MESSAGE = (
    "No completed diagnostic assessment found. "
    "Complete the diagnostic assessment to receive personalized recommendations."
)
MEETS_TARGET_MESSAGE = "Your assessed competencies currently meet their target levels."

_STATUS_RANK = {"Priority Gap": 0, "Moderate Gap": 1}


def _level_value(row: dict) -> int:
    if "current_level_value" in row:
        return int(row["current_level_value"])
    label = str(row.get("current_level") or "")
    if label.startswith("L") and label[1:].isdigit():
        return int(label[1:])
    return 0


def _target_value(row: dict) -> int:
    if "target_level_value" in row:
        return int(row["target_level_value"])
    label = str(row.get("target_level") or "")
    if label.startswith("L") and label[1:].isdigit():
        return int(label[1:])
    return 0


def _gap_by_id(gaps: list[dict]) -> dict[str, dict]:
    return {row["competency_id"]: row for row in gaps}


def _prerequisite_met(programme: Programme, levels: dict[str, int]) -> bool:
    if programme.prerequisite is None:
        return True
    held = levels.get(programme.prerequisite.competency_id)
    if held is None:
        return False
    return held >= programme.prerequisite.min_level


def _matched_gap(programme: Programme, gaps: dict[str, dict]) -> dict | None:
    matches = []
    for competency in programme.competencies:
        row = gaps.get(competency.competency_id)
        if not row or int(row.get("gap") or 0) <= 0:
            continue
        if programme.programme_level <= _level_value(row):
            continue
        matches.append(row)
    if not matches:
        return None
    return min(matches, key=_sort_gap)


def _sort_gap(row: dict) -> tuple:
    return (
        _STATUS_RANK.get(row.get("status") or "", 9),
        -int(row.get("gap") or 0),
        row.get("competency_id") or "",
    )


def _sort_key(item: dict, gap_index: dict[str, int]) -> tuple:
    gap = item["gap_row"]
    programme: Programme = item["programme"]
    current = _level_value(gap)
    return (
        _STATUS_RANK.get(gap.get("status") or "", 9),
        -int(gap.get("gap") or 0),
        0 if item["prerequisite_met"] else 1,
        programme.programme_level - (current + 1),
        gap_index.get(gap["competency_id"], 999),
        programme.title,
        programme.id,
    )


def _reason(programme: Programme, gap: dict) -> str:
    name = gap.get("name") or programme.competencies[0].name
    return (
        f"Addresses {name}, where your demonstrated level is {gap.get('current_level')} "
        f"against a target of {gap.get('target_level')}."
    )


def _recommendation(programme: Programme, gap: dict, met: bool, rank: int) -> dict:
    competency = next(
        row for row in programme.competencies if row.competency_id == gap["competency_id"]
    )
    return {
        "rank": rank,
        "programme_id": programme.id,
        "title": programme.title,
        "source": programme.source,
        "description": programme.description,
        "duration": programme.duration_label,
        "format": programme.format,
        "synthetic": True,
        "matched_competencies": [
            {
                "competency_id": competency.competency_id,
                "name": competency.name,
                "domain": competency.domain,
            }
        ],
        "competency_id": gap["competency_id"],
        "current_level": gap.get("current_level"),
        "target_level": gap.get("target_level"),
        "programme_level": f"L{programme.programme_level}",
        "gap": int(gap.get("gap") or 0),
        "priority": gap.get("priority"),
        "status": gap.get("status"),
        "prerequisite_status": "Met" if met else "Not met",
        "recommendation_reason": _reason(programme, gap),
    }


def rank_programmes(gaps: list[dict], programmes: list[Programme] | None = None) -> dict:
    """Rank catalogue rows from stored gap records. Does not recompute scores."""
    catalogue = list(programmes) if programmes is not None else list(PROGRAMMES)
    open_gaps = [row for row in gaps if int(row.get("gap") or 0) > 0]
    if not open_gaps:
        return {
            "recommendations": [],
            "unmatched_gaps": [],
            "message": MEETS_TARGET_MESSAGE if gaps else None,
        }
    indexed = {row["competency_id"]: index for index, row in enumerate(gaps)}
    levels = {row["competency_id"]: _level_value(row) for row in gaps}
    by_id = _gap_by_id(gaps)
    chosen = []
    matched_ids = set()
    for programme in catalogue:
        gap = _matched_gap(programme, by_id)
        if gap is None:
            continue
        matched_ids.add(gap["competency_id"])
        chosen.append(
            {
                "programme": programme,
                "gap_row": gap,
                "prerequisite_met": _prerequisite_met(programme, levels),
            }
        )
    chosen.sort(key=lambda item: _sort_key(item, indexed))
    recommendations = [
        _recommendation(item["programme"], item["gap_row"], item["prerequisite_met"], index + 1)
        for index, item in enumerate(chosen)
    ]
    unmatched = [
        {
            "competency_id": row["competency_id"],
            "name": row.get("name"),
            "gap": int(row.get("gap") or 0),
        }
        for row in open_gaps
        if row["competency_id"] not in matched_ids
    ]
    return {"recommendations": recommendations, "unmatched_gaps": unmatched, "message": None}


def build_pathway(ranked: dict) -> dict:
    """Sequence ranked programmes. Nothing is marked completed."""
    recommendations = ranked.get("recommendations") or []
    order: list[str] = []
    grouped: dict[str, list[dict]] = {}
    for item in recommendations:
        cid = item["competency_id"]
        if cid not in grouped:
            order.append(cid)
            grouped[cid] = []
        grouped[cid].append(item)
    journeys = []
    for cid in order:
        items = grouped[cid]
        items = sorted(items, key=lambda row: (0 if row["prerequisite_status"] == "Met" else 1, row["rank"]))
        first = items[0]
        steps = [
            {
                "state": "Current",
                "label": first["matched_competencies"][0]["name"],
                "detail": first["current_level"],
            }
        ]
        for index, item in enumerate(items):
            steps.append(
                {
                    "state": "Recommended" if index == 0 else "Next",
                    "label": item["title"],
                    "detail": item["programme_level"],
                    "source": item["source"],
                    "prerequisite_status": item["prerequisite_status"],
                    "recommendation_reason": item["recommendation_reason"],
                    "programme_id": item["programme_id"],
                    "synthetic": True,
                }
            )
        steps.append(
            {
                "state": "Assessment",
                "label": "Follow-up assessment",
                "detail": "Not completed",
            }
        )
        steps.append(
            {
                "state": "Target",
                "label": first["matched_competencies"][0]["name"],
                "detail": first["target_level"],
            }
        )
        journeys.append(
            {
                "competency_id": cid,
                "name": first["matched_competencies"][0]["name"],
                "current_level": first["current_level"],
                "target_level": first["target_level"],
                "gap": first["gap"],
                "priority": first["priority"],
                "status": first["status"],
                "steps": steps,
            }
        )
    return {"journeys": journeys, "message": ranked.get("message")}


def recommend_for_attempt(attempt: dict | None) -> dict:
    generated_at = datetime.now(UTC).isoformat()
    if not attempt or not attempt.get("result"):
        return {
            "learner_id": None if not attempt else attempt.get("learner_id"),
            "assessment_attempt_id": None,
            "generated_at": generated_at,
            "recommendations": [],
            "unmatched_gaps": [],
            "message": NO_ASSESSMENT_MESSAGE,
        }
    result = attempt["result"]
    ranked = rank_programmes(list(result.get("competencies") or []))
    return {
        "learner_id": attempt.get("learner_id"),
        "assessment_attempt_id": attempt.get("attempt_id"),
        "generated_at": generated_at,
        "recommendations": ranked["recommendations"],
        "unmatched_gaps": ranked["unmatched_gaps"],
        "message": ranked["message"],
    }


def catalogue_payload() -> dict:
    programmes = catalogue_rows()
    return {
        "synthetic": False,
        "note": "These courses are the public iGOT Karmayogi catalogue. Opening one here records your answers in STAT-Learn. It does not change your iGOT account.",
        "programmes": programmes,
        "source_url": "https://igotkarmayogi.gov.in/#/",
    }
