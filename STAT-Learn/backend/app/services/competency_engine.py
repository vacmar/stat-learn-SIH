"""Deterministic competency scoring. No model calls."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

LEVELS = (1, 2, 3, 4, 5)
PASS_RATIO = Decimal("0.60")


def display_percent(correct: int, total: int) -> int:
    if total <= 0:
        return 0
    ratio = (Decimal(correct) * Decimal(100)) / Decimal(total)
    return int(ratio.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def level_met(correct: int, attempted: int) -> bool:
    """A level with no attempts is not met. The raw ratio is compared to 0.60."""
    if attempted <= 0:
        return False
    return (Decimal(correct) / Decimal(attempted)) >= PASS_RATIO


def demonstrated_level(by_level: dict[int, tuple[int, int]]) -> int | None:
    """Highest level where that level and every lower level are met.

    None means below L1.
    """
    highest: int | None = None
    for level in LEVELS:
        correct, attempted = by_level.get(level, (0, 0))
        if not level_met(correct, attempted):
            break
        highest = level
    return highest


def gap_and_status(target_level: int, demonstrated: int | None) -> tuple[int, str, str]:
    current_value = 0 if demonstrated is None else demonstrated
    gap = max(0, target_level - current_value)
    if gap == 0:
        return gap, "Meets Target", "Low"
    if gap == 1:
        return gap, "Moderate Gap", "Medium"
    return gap, "Priority Gap", "High"


def level_label(level: int | None) -> str:
    if level is None:
        return "below L1"
    return f"L{level}"


def score_competency(
    *,
    competency_id: str,
    name: str,
    domain: str,
    target_level: int,
    questions: list[dict],
    answers_by_question: dict[str, str],
) -> dict:
    """Score one competency from its items and the stored selected answers.

    Each question dict needs id, level (int), topic, and correct_answer.
    """
    by_level: dict[int, list[dict]] = {level: [] for level in LEVELS}
    for question in questions:
        by_level[int(question["level"])].append(question)

    level_rows = []
    correct_ids: list[str] = []
    incorrect_ids: list[str] = []
    incorrect_topics: list[str] = []
    total_correct = 0
    total = 0

    for level in LEVELS:
        items = by_level[level]
        if not items:
            level_rows.append(
                {
                    "level": f"L{level}",
                    "correct": 0,
                    "attempted": 0,
                    "met": False,
                }
            )
            continue
        correct = 0
        for question in items:
            total += 1
            selected = answers_by_question.get(question["id"], "")
            if selected == question["correct_answer"]:
                correct += 1
                correct_ids.append(question["id"])
            else:
                incorrect_ids.append(question["id"])
                topic = question.get("topic") or ""
                if topic and topic not in incorrect_topics:
                    incorrect_topics.append(topic)
        total_correct += correct
        level_rows.append(
            {
                "level": f"L{level}",
                "correct": correct,
                "attempted": len(items),
                "met": level_met(correct, len(items)),
            }
        )

    counts = {
        level: (row["correct"], row["attempted"])
        for level, row in zip(LEVELS, level_rows, strict=True)
    }
    demonstrated = demonstrated_level(counts)
    gap, status, priority = gap_and_status(target_level, demonstrated)
    return {
        "competency_id": competency_id,
        "name": name,
        "domain": domain,
        "score_ratio": (Decimal(total_correct) / Decimal(total)) if total else Decimal(0),
        "score_percent": display_percent(total_correct, total),
        "current_level": level_label(demonstrated),
        "current_level_value": 0 if demonstrated is None else demonstrated,
        "target_level": level_label(target_level),
        "target_level_value": target_level,
        "gap": gap,
        "status": status,
        "priority": priority,
        "evidence": {
            "correct": total_correct,
            "evaluated": total,
            "incorrect": total - total_correct,
            "by_level": level_rows,
            "correct_question_ids": correct_ids,
            "incorrect_question_ids": incorrect_ids,
            "incorrect_topics": incorrect_topics,
        },
    }


def score_attempt(questions: list[dict], answers_by_question: dict[str, str], targets: list[dict]) -> dict:
    """questions include competency_id, name, domain, level, topic, correct_answer, id."""
    grouped: dict[str, list[dict]] = {}
    for question in questions:
        grouped.setdefault(question["competency_id"], []).append(question)

    results = []
    for target in targets:
        cid = target["competency_id"]
        items = grouped.get(cid, [])
        if not items:
            continue
        results.append(
            score_competency(
                competency_id=cid,
                name=target["name"],
                domain=target["domain"],
                target_level=int(target["target_level"]),
                questions=items,
                answers_by_question=answers_by_question,
            )
        )

    ratios = [row["score_ratio"] for row in results]
    if ratios:
        mean = sum(ratios, Decimal(0)) / Decimal(len(ratios))
        overall = int((mean * Decimal(100)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    else:
        overall = 0

    domains: dict[str, list[Decimal]] = {}
    for row in results:
        domains.setdefault(row["domain"], []).append(row["score_ratio"])
    domain_readiness = []
    for domain, domain_ratios in domains.items():
        domain_mean = sum(domain_ratios, Decimal(0)) / Decimal(len(domain_ratios))
        domain_readiness.append(
            {
                "domain": domain,
                "percent": int((domain_mean * Decimal(100)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)),
                "competencies_assessed": len(domain_ratios),
            }
        )

    serialisable = []
    for row in results:
        copied = dict(row)
        copied["score_ratio"] = float(row["score_ratio"])
        serialisable.append(copied)

    return {
        "overall_score_percent": overall,
        "competencies_assessed": len(serialisable),
        "priority_gap_count": sum(1 for row in serialisable if row["status"] == "Priority Gap"),
        "domain_readiness": domain_readiness,
        "competencies": serialisable,
    }
