"""Generate tailored learning pathways from learner profiles via LLM or mock fallback."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings
from app.core.llm import get_llm
from app.models.structured import (
    CapstoneProject,
    CapstoneRequirement,
    PathGenerateRequest,
    PathwayExplanation,
    PathwayStage,
)
from app.personas.prompts import PATH_GENERATOR_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def _extract_json(text: str) -> dict[str, Any] | None:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except (json.JSONDecodeError, TypeError):
            return None
    return None


def _profile_blob(req: PathGenerateRequest) -> str:
    return " ".join(
        [
            req.target_role or "",
            req.custom_role_title or "",
            req.target_domain or "",
            req.prior_experience or "",
            " ".join(req.goals or []),
            " ".join(req.interests or []),
            " ".join(req.known_skills or []),
        ]
    ).lower()


def _known_set(req: PathGenerateRequest) -> set[str]:
    return {s.strip().lower() for s in (req.known_skills or []) if s and s.strip()}


def _skill_covered(known: set[str], name: str, skills: list[str]) -> bool:
    """True if a known skill clearly matches this stage (avoid java⊂javascript, react⊂RN)."""
    aliases = {name.lower(), *(s.lower() for s in skills)}
    for k in known:
        if len(k) < 3:
            continue
        k_norm = k.replace(".js", "").replace(".", " ").strip().lower()
        for a in aliases:
            a_norm = a.replace(".js", "").replace(".", " ").strip().lower()
            if k_norm == a_norm:
                return True
            # Phrase containment only when both look like multi-token topics
            # and neither is a strict prefix trap (react vs react native)
            if (
                " " in k_norm
                and " " in a_norm
                and (k_norm in a_norm or a_norm in k_norm)
            ):
                return True
            # Single-token: only exact match (already handled) — do not
            # let "react" consume "react native" or "java" consume "javascript"
    return False


def _filter_known_stages(
    stages: list[tuple[str, str, list[str]]], known: set[str]
) -> list[tuple[str, str, list[str]]]:
    """Drop early stages whose primary skill is already known; keep at least 3 stages."""
    if not known or len(stages) <= 3:
        return stages

    kept: list[tuple[str, str, list[str]]] = []
    for idx, (name, rationale, skills) in enumerate(stages):
        # Always keep the final two goal-oriented stages
        if idx >= len(stages) - 2:
            kept.append((name, rationale, skills))
            continue
        if _skill_covered(known, name, skills):
            continue
        kept.append((name, rationale, skills))

    if len(kept) < 3:
        return stages[-3:]
    return kept


def _stage_budget(req: PathGenerateRequest) -> int:
    level = (req.experience_level or "Beginner").lower()
    weekly = req.weekly_time or 10
    if level.startswith("expert"):
        base = 4
    elif level.startswith("inter"):
        base = 5
    else:
        base = 6
    if weekly <= 5:
        base = max(4, base - 1)
    elif weekly >= 15:
        base = min(8, base + 1)
    return base


def _generic_role_path(req: PathGenerateRequest) -> PathwayExplanation:
    """Synthesize a path for ANY free-form role from the seven onboarding answers."""
    role = (req.custom_role_title or req.target_role or "Target Role").strip()
    domain = (req.target_domain or "").strip()
    interests = [i for i in (req.interests or []) if i.strip()]
    known = [s for s in (req.known_skills or []) if s.strip()]
    style = (req.learning_style or "mixed").replace("_", " ")
    level = req.experience_level or "Beginner"
    prior = (req.prior_experience or "").strip()
    budget = _stage_budget(req)

    raw: list[tuple[str, str, list[str]]] = []

    if not level.lower().startswith("expert"):
        raw.append(
            (
                f"Foundations for {role}",
                f"Core concepts a {level.lower()} learner needs before specializing as a {role}."
                + (f" Builds on: {prior}." if prior else ""),
                [f"{role} Foundations"],
            )
        )

    if domain:
        raw.append(
            (
                f"{domain} Context for {role}",
                f"Apply {role} skills in the {domain} domain the learner selected.",
                [domain, role],
            )
        )

    # Stretch known skills toward the role instead of re-teaching them as basics
    for skill in known[:2]:
        raw.append(
            (
                f"{skill} for {role}",
                f"Bridge existing {skill} experience into day-to-day {role} work.",
                [skill, role],
            )
        )

    for interest in interests[:2]:
        raw.append(
            (
                f"{interest} in Practice",
                (
                    f"Lean into the learner's interest in {interest} while progressing toward {role} "
                    f"({style} learning style)."
                ),
                [interest],
            )
        )

    raw.append(
        (
            f"Core {role} Skills",
            f"Primary competencies expected for a working {role}.",
            [role],
        )
    )
    raw.append(
        (
            f"Applied {role} Projects",
            f"Hands-on milestones sized for ~{req.weekly_time or 10} hrs/week.",
            [f"{role} Projects"],
        )
    )
    raw.append(
        (
            f"Portfolio & Interview Prep for {role}",
            f"Package evidence and storytelling so the learner can land {role} opportunities.",
            ["Career", role],
        )
    )

    # Deduplicate by course name while preserving order, then trim to budget
    seen: set[str] = set()
    deduped: list[tuple[str, str, list[str]]] = []
    for item in raw:
        key = item[0].lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    if len(deduped) > budget:
        # Keep first foundation-ish stages and always keep last two
        head = deduped[: max(1, budget - 2)]
        tail = deduped[-2:]
        merged = head + [t for t in tail if t not in head]
        deduped = merged[:budget]

    stages = _stages_from_tuples(deduped)
    interest_bit = interests[0] if interests else domain or role
    return PathwayExplanation(
        summary=(
            f"A personalized map for {req.name or 'you'} to become a {role}, "
            f"shaped by your onboarding answers ({level}, {style}, "
            f"{req.weekly_time or 10} hrs/week)."
        ),
        target_role=role,
        stages=stages,
        gap_analysis_summary=(
            f"Skips pure re-teaching of known skills ({', '.join(known) or 'none listed'}) "
            f"and sequences foundations → domain ({domain or 'general'}) → role practice → portfolio."
        ),
        estimated_total_hours=float((req.weekly_time or 10) * max(4, len(stages))),
        tools_used=["mock_path_generator", "generic_role_synth"],
        capstone=CapstoneProject(
            title=f"Capstone: {role} Showcase",
            description=(
                f"Ship a small portfolio project that demonstrates readiness for a {role} role"
                + (f" in {domain}" if domain else "")
                + (f", highlighting {interest_bit}" if interest_bit else "")
                + "."
            ),
            requirements=[
                CapstoneRequirement(
                    requirement_id="req_role",
                    description=f"Must clearly target {role} competencies",
                    mandatory=True,
                ),
                CapstoneRequirement(
                    requirement_id="req_demo",
                    description="Must include a runnable demo or documented walkthrough",
                    mandatory=True,
                ),
                CapstoneRequirement(
                    requirement_id="req_readme",
                    description="Must explain design choices and what you learned",
                    mandatory=True,
                ),
                CapstoneRequirement(
                    requirement_id="req_interest",
                    description=f"Optional: emphasize {interest_bit}",
                    mandatory=False,
                ),
            ],
        ),
    )


def mock_generate_pathway(req: PathGenerateRequest) -> PathwayExplanation:
    """Profile-aware pathway when LLM is mock or unavailable — still role-specific."""
    blob = _profile_blob(req)
    role_id = (req.target_role_id or "").lower()

    mobile_hints = (
        "android",
        "ios",
        "mobile",
        "react native",
        "flutter",
    )
    if any(k in blob for k in mobile_hints):
        return _mobile_path(req)

    if role_id == "role_fe" or any(
        k in blob for k in ("frontend", "front-end", "front end", "ui/ux", " next.js")
    ):
        return _frontend_path(req)

    if role_id == "role_de" or any(
        k in blob for k in ("data engineer", "etl", "warehouse", "data pipeline")
    ):
        return _data_path(req)

    if role_id in {"role_be", "role_mlops"} or any(
        k in blob for k in ("backend", "fastapi", "api engineer", "server engineer")
    ):
        return _backend_path(req)

    if role_id == "role_ai" or any(
        k in blob for k in ("ai engineer", "machine learning", "llm", "ml engineer")
    ):
        # Prefer generic synthesis with AI-flavored title rather than forcing Python/SQL only
        return _generic_role_path(req)

    # Any free-text Other role (or unknown catalog): synthesize from the 7 answers
    return _generic_role_path(req)


def _stages_from_tuples(
    tuples: list[tuple[str, str, list[str]]],
) -> list[PathwayStage]:
    return [
        PathwayStage(
            stage_number=i + 1,
            course_name=name,
            rationale=rationale,
            target_skills=skills,
        )
        for i, (name, rationale, skills) in enumerate(tuples)
    ]


def _mobile_path(req: PathGenerateRequest) -> PathwayExplanation:
    known = _known_set(req)
    raw = [
        (
            "JavaScript Fundamentals",
            "Core language skills for React Native and mobile UI logic.",
            ["JavaScript"],
        ),
        (
            "React Essentials",
            "Component model and state management shared with React Native.",
            ["React"],
        ),
        (
            "React Native Basics",
            "Cross-platform mobile app structure, navigation, and native bridges.",
            ["React Native"],
        ),
        (
            "Android App Foundations",
            "Platform patterns, responsiveness, and release basics for Android.",
            ["Android"],
        ),
        (
            "Mobile UI/UX Patterns",
            "Polish layouts and interaction patterns for mobile screens.",
            ["UI/UX"],
        ),
    ]
    stages = _stages_from_tuples(_filter_known_stages(raw, known))
    role = req.target_role or "Mobile Developer"
    return PathwayExplanation(
        summary=f"A mobile-first path toward {role}, ordered by prerequisite skills.",
        target_role=role,
        stages=stages,
        gap_analysis_summary=(
            "Closes gaps from language foundations through React Native and Android "
            "while respecting skills you already listed."
        ),
        estimated_total_hours=float((req.weekly_time or 10) * max(4, len(stages))),
        tools_used=["mock_path_generator"],
        capstone=CapstoneProject(
            title="Build a Mobile Screen Flow",
            description=(
                "Create a React Native app with navigation and two polished screens "
                "aligned to your Android / mobile goal."
            ),
            requirements=[
                CapstoneRequirement(
                    requirement_id="req_rn",
                    description="Must use React Native",
                    mandatory=True,
                ),
                CapstoneRequirement(
                    requirement_id="req_nav",
                    description="Must include screen navigation",
                    mandatory=True,
                ),
                CapstoneRequirement(
                    requirement_id="req_responsive",
                    description="Must demonstrate responsive mobile layout",
                    mandatory=True,
                ),
                CapstoneRequirement(
                    requirement_id="req_polish",
                    description="Optional: add a simple animation or gesture",
                    mandatory=False,
                ),
            ],
        ),
    )


def _frontend_path(req: PathGenerateRequest) -> PathwayExplanation:
    known = _known_set(req)
    raw = [
        (
            "HTML & CSS Foundations",
            "Structure and layout for modern web UIs.",
            ["HTML", "CSS"],
        ),
        (
            "JavaScript Fundamentals",
            "Language essentials for interactive interfaces.",
            ["JavaScript"],
        ),
        (
            "React Essentials",
            "Build component-driven UIs for your frontend goal.",
            ["React"],
        ),
        (
            "Frontend State & Data Fetching",
            "Wire UI to APIs and manage client state cleanly.",
            ["Frontend"],
        ),
        (
            "UI/UX for Web Apps",
            "Accessibility, responsiveness, and visual polish.",
            ["UI/UX"],
        ),
    ]
    stages = _stages_from_tuples(_filter_known_stages(raw, known))
    role = req.target_role or "Frontend Developer"
    return PathwayExplanation(
        summary=f"A frontend path tailored for {role}.",
        target_role=role,
        stages=stages,
        gap_analysis_summary="Builds from web fundamentals to React and polished UI delivery.",
        estimated_total_hours=float((req.weekly_time or 10) * max(4, len(stages))),
        tools_used=["mock_path_generator"],
        capstone=CapstoneProject(
            title="Build a Responsive Web App",
            description="Ship a small React app with two routes and clean UI.",
            requirements=[
                CapstoneRequirement(
                    requirement_id="req_react",
                    description="Must use React",
                    mandatory=True,
                ),
                CapstoneRequirement(
                    requirement_id="req_routes",
                    description="Must include at least two routes/pages",
                    mandatory=True,
                ),
                CapstoneRequirement(
                    requirement_id="req_responsive",
                    description="Must be responsive on mobile widths",
                    mandatory=True,
                ),
            ],
        ),
    )


def _backend_path(req: PathGenerateRequest) -> PathwayExplanation:
    known = _known_set(req)
    raw = [
        (
            "Python Basics",
            "Language foundations for APIs and services.",
            ["Python"],
        ),
        (
            "SQL Basics",
            "Query and model data for backend services.",
            ["SQL"],
        ),
        (
            "HTTP & REST APIs",
            "Design endpoints, status codes, and JSON contracts.",
            ["REST"],
        ),
        (
            "FastAPI Essentials",
            "Build production-ready Python APIs.",
            ["FastAPI"],
        ),
        (
            "Auth & Testing for APIs",
            "Secure endpoints and verify behavior with tests.",
            ["API Auth"],
        ),
    ]
    stages = _stages_from_tuples(_filter_known_stages(raw, known))
    role = req.target_role or "Backend Developer"
    return PathwayExplanation(
        summary=f"A backend/API path toward {role}.",
        target_role=role,
        stages=stages,
        gap_analysis_summary="Sequences language, data, and API skills needed for service work.",
        estimated_total_hours=float((req.weekly_time or 10) * max(4, len(stages))),
        tools_used=["mock_path_generator"],
        capstone=CapstoneProject(
            title="Build a Simple API",
            description="Create a FastAPI application with two endpoints.",
            requirements=[
                CapstoneRequirement(
                    requirement_id="req_fastapi",
                    description="Must use FastAPI",
                    mandatory=True,
                ),
                CapstoneRequirement(
                    requirement_id="req_health",
                    description="Must have /health endpoint",
                    mandatory=True,
                ),
                CapstoneRequirement(
                    requirement_id="req_json",
                    description="Must return JSON",
                    mandatory=True,
                ),
            ],
        ),
    )


def _data_path(req: PathGenerateRequest) -> PathwayExplanation:
    known = _known_set(req)
    raw = [
        ("Python Basics", "Scripting foundation for data work.", ["Python"]),
        ("SQL Basics", "Query warehouses and transactional stores.", ["SQL"]),
        (
            "Data Modeling & ETL Patterns",
            "Shape pipelines and transformations.",
            ["ETL"],
        ),
        (
            "Cloud Data Engineering",
            "Deploy and operate data workloads in the cloud.",
            ["Cloud"],
        ),
    ]
    stages = _stages_from_tuples(_filter_known_stages(raw, known))
    role = req.target_role or "Data Engineer"
    return PathwayExplanation(
        summary=f"A data engineering path toward {role}.",
        target_role=role,
        stages=stages,
        gap_analysis_summary="Closes gaps in Python, SQL, ETL, and cloud data skills.",
        estimated_total_hours=float((req.weekly_time or 10) * max(4, len(stages))),
        tools_used=["mock_path_generator"],
        capstone=CapstoneProject(
            title="Build a Mini ETL Pipeline",
            description="Ingest, transform, and load a small dataset with documented SQL.",
            requirements=[
                CapstoneRequirement(
                    requirement_id="req_etl",
                    description="Must implement extract-transform-load steps",
                    mandatory=True,
                ),
                CapstoneRequirement(
                    requirement_id="req_sql",
                    description="Must include SQL transformations",
                    mandatory=True,
                ),
            ],
        ),
    )


def _parse_pathway(
    data: dict[str, Any], req: PathGenerateRequest
) -> PathwayExplanation:
    stages_raw = data.get("stages") or []
    stages: list[PathwayStage] = []
    for i, s in enumerate(stages_raw):
        if isinstance(s, dict):
            stages.append(
                PathwayStage(
                    stage_number=int(s.get("stage_number", i + 1)),
                    course_name=str(
                        s.get("course_name") or s.get("title") or f"Stage {i + 1}"
                    ),
                    rationale=str(s.get("rationale") or "Curriculum progression"),
                    target_skills=list(s.get("target_skills") or []),
                )
            )
        else:
            stages.append(
                PathwayStage(
                    stage_number=i + 1,
                    course_name=str(s),
                    rationale="Curriculum progression",
                    target_skills=[],
                )
            )

    capstone = None
    cap_raw = data.get("capstone")
    if isinstance(cap_raw, dict) and cap_raw.get("title"):
        reqs = []
        for j, r in enumerate(cap_raw.get("requirements") or []):
            if isinstance(r, dict):
                reqs.append(
                    CapstoneRequirement(
                        requirement_id=str(r.get("requirement_id") or f"req_{j + 1}"),
                        description=str(r.get("description") or "Requirement"),
                        mandatory=bool(r.get("mandatory", True)),
                    )
                )
            else:
                reqs.append(
                    CapstoneRequirement(
                        requirement_id=f"req_{j + 1}",
                        description=str(r),
                        mandatory=True,
                    )
                )
        capstone = CapstoneProject(
            title=str(cap_raw["title"]),
            description=str(cap_raw.get("description") or ""),
            requirements=reqs,
        )

    if not stages:
        return mock_generate_pathway(req)

    return PathwayExplanation(
        summary=str(data.get("summary") or f"Personalized path for {req.target_role}"),
        target_role=str(data.get("target_role") or req.target_role),
        stages=stages,
        gap_analysis_summary=str(
            data.get("gap_analysis_summary")
            or "Stages close skill gaps toward the stated goal."
        ),
        estimated_total_hours=float(data.get("estimated_total_hours") or 40.0),
        tools_used=list(data.get("tools_used") or ["llm_path_generator"]),
        capstone=capstone or mock_generate_pathway(req).capstone,
    )


def _build_user_prompt(req: PathGenerateRequest) -> str:
    schema_hint = {
        "summary": "string",
        "target_role": "string",
        "stages": [
            {
                "stage_number": 1,
                "course_name": "string",
                "rationale": "string",
                "target_skills": ["string"],
            }
        ],
        "gap_analysis_summary": "string",
        "estimated_total_hours": 40,
        "capstone": {
            "title": "string",
            "description": "string",
            "requirements": [
                {
                    "requirement_id": "req_1",
                    "description": "string",
                    "mandatory": True,
                }
            ],
        },
    }
    answers = {
        "1_name": req.name,
        "2_target_role": req.target_role,
        "2_custom_role_title": req.custom_role_title,
        "2_domain": req.target_domain,
        "3_experience_level": req.experience_level,
        "3_prior_experience": req.prior_experience,
        "4_known_skills": req.known_skills,
        "5_interests": req.interests,
        "6_learning_style": req.learning_style,
        "6_weekly_time_hours": req.weekly_time,
        "7_goals": req.goals,
    }
    return (
        "Generate a tailored learning pathway from these seven onboarding answers.\n"
        "The target role may be any free-text career goal — map a perfect mastery path for THAT role.\n\n"
        f"Onboarding answers:\n{json.dumps(answers, indent=2)}\n\n"
        f"Full profile JSON:\n{req.model_dump_json(indent=2)}\n\n"
        f"Respond with JSON matching this shape:\n{json.dumps(schema_hint, indent=2)}"
    )


async def generate_pathway(req: PathGenerateRequest) -> PathwayExplanation:
    """Author a pathway via LLM, falling back to profile-aware mock on failure."""
    if settings.llm_provider.lower() == "mock":
        return mock_generate_pathway(req)

    try:
        llm = get_llm(temperature=0.3)
        messages = [
            SystemMessage(content=PATH_GENERATOR_SYSTEM_PROMPT),
            HumanMessage(content=_build_user_prompt(req)),
        ]
        response = await llm.ainvoke(messages)
        content = str(response.content) if response.content else ""
        parsed = _extract_json(content)
        if not parsed:
            logger.warning("Path generator LLM returned non-JSON; using mock fallback")
            return mock_generate_pathway(req)
        return _parse_pathway(parsed, req)
    except Exception as e:
        logger.warning("Path generator LLM failed (%s); using mock fallback", e)
        return mock_generate_pathway(req)
