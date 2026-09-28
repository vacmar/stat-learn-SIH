"""Public iGOT Karmayogi course list. Titles and providers come from their public search.

The study check is recorded in this app. It does not update an iGOT transcript.
"""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime

from fastapi import HTTPException

from app.repository import sqlite_db

SEARCH_URL = "https://portal.igotkarmayogi.gov.in/api/content/v1/search"
COURSE_URL = "https://portal.igotkarmayogi.gov.in/app/toc/{course_id}/overview"
QUERIES = (
    "statistics",
    "statistical survey",
    "sampling",
    "census",
    "national accounts",
    "data quality",
    "data analysis",
)
BANDS = ("Under 1 hour", "1 to 3 hours", "3 to 6 hours", "Over 6 hours")


def _duration_label(seconds: int | None) -> str:
    if not seconds or seconds <= 0:
        return "Length listed on iGOT"
    minutes = max(1, round(seconds / 60))
    if minutes < 60:
        return f"{minutes} minutes"
    hours = minutes / 60
    if hours < 10:
        shown = round(hours, 1)
        text = str(int(shown)) if shown == int(shown) else str(shown)
        return f"{text} hours"
    return f"{round(hours)} hours"


def _band(seconds: int | None) -> str:
    if not seconds or seconds < 3600:
        return BANDS[0]
    if seconds < 3 * 3600:
        return BANDS[1]
    if seconds < 6 * 3600:
        return BANDS[2]
    return BANDS[3]


def _clean_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    found = []
    for item in value:
        text = str(item).strip()
        if text and text not in found:
            found.append(text)
    return found


def _search(query: str, limit: int = 20) -> list[dict]:
    payload = {
        "request": {
            "filters": {"status": ["Live"], "primaryCategory": ["Course"]},
            "query": query,
            "offset": 0,
            "limit": limit,
            "fields": ["name", "identifier", "source", "organisation", "duration", "language", "keywords", "competencies_v6"],
        }
    }
    raw = subprocess.check_output(
        [
            "curl",
            "-sS",
            "--max-time",
            "30",
            "-X",
            "POST",
            SEARCH_URL,
            "-H",
            "Content-Type: application/json",
            "-H",
            "Accept: application/json",
            "-H",
            "X-Channel-Id: 0133783095823810560",
            "-d",
            json.dumps(payload),
        ],
        text=True,
    )
    body = json.loads(raw)
    return list(body.get("result", {}).get("content") or [])


def _normalise(row: dict) -> dict | None:
    course_id = str(row.get("identifier") or "").strip()
    name = str(row.get("name") or "").strip()
    if not course_id.startswith("do_") or not name:
        return None
    provider = str(row.get("source") or "").strip()
    if not provider:
        orgs = _clean_list(row.get("organisation"))
        provider = orgs[0] if orgs else "iGOT Karmayogi"
    competency = ""
    themes = row.get("competencies_v6") or []
    if isinstance(themes, list) and themes:
        first = themes[0] if isinstance(themes[0], dict) else {}
        competency = str(first.get("competencySubThemeName") or first.get("competencyThemeName") or "").strip()
    keywords = _clean_list(row.get("keywords"))[:6]
    if competency and competency not in keywords:
        keywords.insert(0, competency)
    languages = _clean_list(row.get("language"))
    try:
        seconds = int(float(row.get("duration") or 0))
    except (TypeError, ValueError):
        seconds = 0
    return {
        "course_id": course_id,
        "name": name,
        "provider": provider,
        "duration_seconds": seconds or None,
        "language": ", ".join(languages) or "Not listed",
        "keywords": json.dumps(keywords[:6]),
        "competency": competency or None,
        "external_url": COURSE_URL.format(course_id=course_id),
    }


def refresh_igot_catalogue() -> int:
    seen: dict[str, dict] = {}
    for query in QUERIES:
        for row in _search(query):
            item = _normalise(row)
            if item and item["course_id"] not in seen:
                seen[item["course_id"]] = item
            if len(seen) >= 60:
                break
        if len(seen) >= 60:
            break
    if not seen:
        raise RuntimeError("iGOT search returned no courses")
    sqlite_db.replace_igot_courses(list(seen.values()), datetime.now(UTC).isoformat())
    return len(seen)


def ensure_igot_catalogue() -> list[dict]:
    rows = sqlite_db.list_igot_courses()
    if rows:
        return rows
    refresh_igot_catalogue()
    return sqlite_db.list_igot_courses()


def catalogue_rows() -> list[dict]:
    rows = ensure_igot_catalogue()
    public = []
    for row in rows:
        seconds = row.get("duration_seconds") or 0
        hours = round(seconds / 3600, 1) if seconds else 0
        keywords = row.get("keywords") or []
        competency = row.get("competency") or (keywords[0] if keywords else "iGOT course")
        public.append(
            {
                "id": row["course_id"],
                "title": row["name"],
                "source": "iGOT",
                "description": f"Published on iGOT Karmayogi by {row['provider']}.",
                "competencies": [{"competency_id": row["course_id"], "name": competency, "domain": "iGOT"}],
                "domains": ["iGOT"],
                "level": row["language"],
                "duration_hours": hours,
                "duration": _duration_label(seconds),
                "format": row["provider"],
                "prerequisites": [],
                "synthetic": False,
                "external_url": row["external_url"],
                "keywords": keywords,
            }
        )
    return public


def _shift(options: list[str], seed: str) -> list[str]:
    if not options:
        return options
    offset = sum(ord(char) for char in seed) % len(options)
    return options[offset:] + options[:offset]


def _course(course_id: str) -> dict:
    for row in ensure_igot_catalogue():
        if row["course_id"] == course_id:
            return row
    raise HTTPException(status_code=404, detail="Course not found")


def questions_for(course_id: str) -> list[dict]:
    course = _course(course_id)
    others = [row for row in ensure_igot_catalogue() if row["course_id"] != course_id]
    providers = [course["provider"]]
    for row in others:
        if row["provider"] not in providers:
            providers.append(row["provider"])
        if len(providers) == 4:
            break
    while len(providers) < 4:
        providers.append(f"Another provider {len(providers)}")
    keywords = list(course.get("keywords") or []) or ["This course"]
    other_keywords = []
    own = set(keywords)
    for row in others:
        for word in row.get("keywords") or []:
            if word not in own and word not in other_keywords:
                other_keywords.append(word)
            if len(other_keywords) >= 3:
                break
        if len(other_keywords) >= 3:
            break
    while len(other_keywords) < 3:
        other_keywords.append(f"Another topic {len(other_keywords)}")
    seconds = course.get("duration_seconds") or 0
    correct_band = _band(seconds)
    return [
        {
            "id": f"{course_id}-provider",
            "prompt": "Which organisation publishes this course on iGOT?",
            "options": _shift(providers[:4], course_id + "provider"),
            "answer": course["provider"],
        },
        {
            "id": f"{course_id}-topic",
            "prompt": "Which topic is listed on this course?",
            "options": _shift([keywords[0], *other_keywords[:3]], course_id + "topic"),
            "answer": keywords[0],
        },
        {
            "id": f"{course_id}-length",
            "prompt": "How long is this course on the public iGOT listing?",
            "options": _shift(list(BANDS), course_id + "length"),
            "answer": correct_band,
        },
    ]


def public_course(course_id: str) -> dict:
    course = _course(course_id)
    questions = questions_for(course_id)
    keywords = course.get("keywords") or []
    topic = ", ".join(keywords[:4]) or "the topic shown on iGOT"
    return {
        "id": course["course_id"],
        "title": course["name"],
        "source": "iGOT",
        "description": f"Published on iGOT Karmayogi by {course['provider']}.",
        "level": course.get("language") or "",
        "duration": _duration_label(course.get("duration_seconds") or 0),
        "external_url": course["external_url"],
        "lessons": [
            f"This course is on iGOT Karmayogi, from {course['provider']}.",
            f"The public listing names these topics: {topic}.",
            "Read the listing, answer the three checks, and open the course on iGOT for the full modules. Finishing here does not change your iGOT account.",
        ],
        "questions": [{"id": item["id"], "prompt": item["prompt"], "options": item["options"]} for item in questions],
        "pass_rule": "At least 2 of 3 answers must be correct.",
    }
