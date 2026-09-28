"""Synthetic iGOT, NSSTA, and TPAC catalogue. Not a live government feed."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Prerequisite:
    competency_id: str
    min_level: int


@dataclass(frozen=True)
class ProgrammeCompetency:
    competency_id: str
    name: str
    domain: str


@dataclass(frozen=True)
class Programme:
    id: str
    title: str
    source: str
    description: str
    competencies: tuple[ProgrammeCompetency, ...]
    programme_level: int
    duration_hours: int
    format: str
    prerequisite: Prerequisite | None
    synthetic: bool = True

    @property
    def duration_label(self) -> str:
        return f"{self.duration_hours} hours"


def _programme(
    pid: str,
    title: str,
    source: str,
    description: str,
    competency_id: str,
    name: str,
    domain: str,
    programme_level: int,
    duration_hours: int,
    fmt: str,
    prerequisite: Prerequisite | None,
) -> Programme:
    return Programme(
        id=pid,
        title=title,
        source=source,
        description=description,
        competencies=(ProgrammeCompetency(competency_id, name, domain),),
        programme_level=programme_level,
        duration_hours=duration_hours,
        format=fmt,
        prerequisite=prerequisite,
    )


PROGRAMMES: tuple[Programme, ...] = (
    _programme(
        "igot-official-analysis",
        "Analysis of official statistical datasets",
        "iGOT",
        "Synthetic module on interpreting official tables at the next level after L2.",
        "stat-data-analysis",
        "Statistical Data Analysis",
        "STAT",
        3,
        12,
        "Self-paced module",
        Prerequisite("stat-data-analysis", 2),
    ),
    _programme(
        "igot-advanced-analysis",
        "Advanced interpretation of official releases",
        "iGOT",
        "Synthetic module for L4 interpretation. It assumes L3 practice is already in place.",
        "stat-data-analysis",
        "Statistical Data Analysis",
        "STAT",
        4,
        8,
        "Self-paced module",
        Prerequisite("stat-data-analysis", 3),
    ),
    _programme(
        "nssta-survey-practicum",
        "Survey methodology practicum",
        "NSSTA",
        "Synthetic instructor-led practicum on household-survey coverage at L3.",
        "stat-survey-methodology",
        "Survey Methodology",
        "STAT",
        3,
        8,
        "Instructor-led programme",
        Prerequisite("stat-survey-methodology", 2),
    ),
    _programme(
        "tpac-data-quality",
        "Data quality frameworks for published tables",
        "TPAC",
        "Synthetic workshop on release checks for officers already at L3.",
        "stat-data-quality",
        "Data Quality",
        "STAT",
        4,
        6,
        "Blended workshop",
        Prerequisite("stat-data-quality", 3),
    ),
    _programme(
        "nssta-sampling-note",
        "Sample allocation across strata",
        "NSSTA",
        "Synthetic note on stratum allocation. It is not part of the diagnostic competencies.",
        "stat-sampling",
        "Sampling Design",
        "STAT",
        4,
        5,
        "Self-paced module",
        Prerequisite("stat-sampling", 3),
    ),
    _programme(
        "igot-sdg",
        "SDG indicator disaggregation",
        "iGOT",
        "Synthetic workshop on indicator disaggregation.",
        "stat-sdg",
        "SDG Indicators",
        "STAT",
        3,
        10,
        "Blended workshop",
        None,
    ),
    _programme(
        "nssta-reproducible-tables",
        "Reproducible official tables",
        "NSSTA",
        "Synthetic programme on documented table releases.",
        "tech-statistical-computing",
        "Statistical Computing Practice",
        "TECH",
        4,
        9,
        "Instructor-led programme",
        Prerequisite("tech-statistical-computing", 3),
    ),
    _programme(
        "tpac-geospatial",
        "Geospatial briefing for statistical offices",
        "TPAC",
        "Synthetic briefing on geospatial statistics.",
        "tech-gis",
        "Geospatial Statistics",
        "TECH",
        3,
        4,
        "Instructor-led programme",
        None,
    ),
    _programme(
        "igot-revisions",
        "Communicating statistical revisions",
        "iGOT",
        "Synthetic module on revision notices.",
        "beh-communication",
        "Official Communication",
        "BEH",
        4,
        3,
        "Self-paced module",
        Prerequisite("beh-communication", 3),
    ),
    _programme(
        "tpac-coordination",
        "Coordination with training counterparts",
        "TPAC",
        "Synthetic workshop on coordination with training counterparts.",
        "beh-coordination",
        "Stakeholder Coordination",
        "BEH",
        4,
        6,
        "Blended workshop",
        None,
    ),
)

PROGRAMME_BY_ID = {item.id: item for item in PROGRAMMES}


def public_programme(item: Programme) -> dict:
    return {
        "id": item.id,
        "title": item.title,
        "source": item.source,
        "description": item.description,
        "competencies": [
            {"competency_id": row.competency_id, "name": row.name, "domain": row.domain}
            for row in item.competencies
        ],
        "domains": sorted({row.domain for row in item.competencies}),
        "level": f"L{item.programme_level}",
        "programme_level": item.programme_level,
        "duration_hours": item.duration_hours,
        "duration": item.duration_label,
        "format": item.format,
        "prerequisites": (
            [
                {
                    "competency_id": item.prerequisite.competency_id,
                    "min_level": f"L{item.prerequisite.min_level}",
                }
            ]
            if item.prerequisite
            else []
        ),
        "synthetic": True,
    }
