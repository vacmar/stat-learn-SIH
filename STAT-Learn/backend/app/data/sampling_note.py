"""Synthetic sampling note. Demo source, not an official government publication."""

from __future__ import annotations

from dataclasses import dataclass

DOCUMENT_ID = "mat-sampling-note"


@dataclass(frozen=True)
class SourceChunk:
    id: str
    document_id: str
    section: str
    text: str
    competencies: tuple[str, ...]


@dataclass(frozen=True)
class SourceDocument:
    id: str
    title: str
    source_label: str
    filename: str
    status: str
    summary: str


DOCUMENT = SourceDocument(
    id=DOCUMENT_ID,
    title="Sampling concepts for official surveys",
    source_label="Demo source",
    filename="synthetic-sampling-note.txt",
    status="Ready",
    summary=(
        "A short original note on coverage, frames, and stratum allocation. "
        "It is demo material, not an official course file."
    ),
)

CHUNKS: tuple[SourceChunk, ...] = (
    SourceChunk(
        id="chunk-coverage",
        document_id=DOCUMENT_ID,
        section="Coverage",
        text=(
            "If newly formed dwellings are missing from the frame, households in those "
            "dwellings have no chance of selection."
        ),
        competencies=("stat-survey-methodology",),
    ),
    SourceChunk(
        id="chunk-stratified",
        document_id=DOCUMENT_ID,
        section="Stratified sampling",
        text=(
            "Stratified sampling divides the population into subgroups and selects within "
            "each subgroup so that each subgroup can be represented in the sample."
        ),
        competencies=("stat-survey-methodology",),
    ),
    SourceChunk(
        id="chunk-allocation",
        document_id=DOCUMENT_ID,
        section="Allocation",
        text=(
            "Allocation notes should state the stratum, the allocated size, and the rule "
            "used to arrive at that size."
        ),
        competencies=("stat-survey-methodology",),
    ),
)

CHUNK_BY_ID = {item.id: item for item in CHUNKS}

KNOWN_COMPETENCIES = {
    "stat-data-analysis": ("Statistical Data Analysis", "STAT"),
    "stat-survey-methodology": ("Survey Methodology", "STAT"),
    "stat-data-quality": ("Data Quality", "STAT"),
}


def chunks_for_competency(competency_id: str) -> list[SourceChunk]:
    matched = [item for item in CHUNKS if competency_id in item.competencies]
    if matched:
        return matched
    return [item for item in CHUNKS if "stat-survey-methodology" in item.competencies]


def public_document() -> dict:
    return {
        "id": DOCUMENT.id,
        "title": DOCUMENT.title,
        "source": DOCUMENT.source_label,
        "filename": DOCUMENT.filename,
        "status": DOCUMENT.status,
        "summary": DOCUMENT.summary,
        "synthetic": True,
        "chunks": len(CHUNKS),
        "sections": [chunk.section for chunk in CHUNKS],
        "added": "Demo seed",
    }
