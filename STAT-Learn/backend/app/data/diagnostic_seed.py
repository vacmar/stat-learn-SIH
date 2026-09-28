"""Canonical diagnostic for the screening competency engine.

Correct options stay on the server. The first option is correct unless a test
overrides the index. The screening answer pattern is the set of indexes in
SCREENING_ANSWER_INDEX; every other item uses index 0.
"""

from __future__ import annotations

from dataclasses import dataclass

ASSESSMENT_ID = "diagnostic-statistical-officer"
ASSESSMENT_TITLE = "Diagnostic Competency Assessment"

DEMO_LEARNER_ID = "learner_arun_kumar"
DEMO_LEARNER_TOKEN = "arun-kumar"
DEMO_LEARNER_HEADER = "X-Statlearn-Demo-Learner"


@dataclass(frozen=True)
class DiagnosticQuestion:
    id: str
    competency_id: str
    competency_name: str
    domain: str
    level: int
    topic: str
    prompt: str
    options: tuple[str, ...]
    correct_index: int

    @property
    def correct_answer(self) -> str:
        return self.options[self.correct_index]


@dataclass(frozen=True)
class CompetencyTarget:
    competency_id: str
    name: str
    domain: str
    domain_label: str
    target_level: int


COMPETENCIES: tuple[CompetencyTarget, ...] = (
    CompetencyTarget("stat-data-analysis", "Statistical Data Analysis", "STAT", "Statistical", 4),
    CompetencyTarget("stat-survey-methodology", "Survey Methodology", "STAT", "Statistical", 3),
    CompetencyTarget("stat-data-quality", "Data Quality", "STAT", "Statistical", 4),
)

TARGET_BY_ID = {item.competency_id: item for item in COMPETENCIES}


def _q(
    qid: str,
    competency_id: str,
    level: int,
    topic: str,
    prompt: str,
    options: tuple[str, ...],
) -> DiagnosticQuestion:
    target = TARGET_BY_ID[competency_id]
    return DiagnosticQuestion(
        id=qid,
        competency_id=competency_id,
        competency_name=target.name,
        domain=target.domain,
        level=level,
        topic=topic,
        prompt=prompt,
        options=options,
        correct_index=0,
    )


QUESTIONS: tuple[DiagnosticQuestion, ...] = (
    _q(
        "sda-l1-a",
        "stat-data-analysis",
        1,
        "reading a table",
        "What does the reference period in a statistical table tell the reader?",
        (
            "The time span the figures describe",
            "The name of the officer who typed the table",
            "The colour used in the chart",
            "The software brand that stored the file",
        ),
    ),
    _q(
        "sda-l1-b",
        "stat-data-analysis",
        1,
        "reading a table",
        "A cell in an official table is blank with a footnote that the value is not available. What should a reader conclude?",
        (
            "The figure was not published for that cell",
            "The value is zero",
            "The series has been discontinued forever",
            "The footnote is decorative and can be ignored",
        ),
    ),
    _q(
        "sda-l2-a",
        "stat-data-analysis",
        2,
        "comparing figures",
        "Two annual figures can be compared directly when which condition holds?",
        (
            "They use the same definition, unit, and reference convention",
            "They appear in the same colour on the page",
            "They were released on the same weekday",
            "They are both larger than the previous year",
        ),
    ),
    _q(
        "sda-l3-a",
        "stat-data-analysis",
        3,
        "statistical interpretation",
        "A published table shows a sharp change after a classification update. What should the statistical officer do before describing the change as a movement in the underlying series?",
        (
            "Confirm whether the classification break has been adjusted or footnoted",
            "Treat every large change as a seasonal effect",
            "Replace the table with an average of the last five years",
            "Suppress the series until the next census",
        ),
    ),
    _q(
        "sda-l3-b",
        "stat-data-analysis",
        3,
        "statistical interpretation",
        "An index changes because the base period was updated. How should that change be described?",
        (
            "As a rebasing effect unless a comparable series is also shown",
            "As proof that the underlying activity doubled",
            "As a data-entry error that must be deleted",
            "As a behavioural competency gap",
        ),
    ),
    _q(
        "surv-l1-a",
        "stat-survey-methodology",
        1,
        "survey basics",
        "In a household survey, who is the usual unit listed on the sampling frame?",
        (
            "A dwelling or household that can be selected",
            "A chart title",
            "A training programme",
            "A press-note sentence",
        ),
    ),
    _q(
        "surv-l2-a",
        "stat-survey-methodology",
        2,
        "coverage",
        "Why is a list of dwellings prepared before selection?",
        (
            "So each listed dwelling has a known chance of being selected",
            "So the questionnaire can be shortened",
            "So results can skip fieldwork",
            "So the chart uses fewer colours",
        ),
    ),
    _q(
        "surv-l3-a",
        "stat-survey-methodology",
        3,
        "sampling concepts",
        "A household survey frame excludes newly formed dwellings in one district. Which description fits the risk?",
        (
            "Coverage error that can bias estimates for that district",
            "A labelling convention that only affects the questionnaire layout",
            "A presentation choice for the press note",
            "A behavioural competency for field supervisors",
        ),
    ),
    _q(
        "dq-l1-a",
        "stat-data-quality",
        1,
        "basic checks",
        "Before a table is circulated, which check is a basic quality step?",
        (
            "Confirm the title, unit, and reference period are present",
            "Remove every footnote",
            "Round every number to zero",
            "Replace the source with the author's name",
        ),
    ),
    _q(
        "dq-l2-a",
        "stat-data-quality",
        2,
        "consistency",
        "A row total does not equal the sum of the published cells. What is the appropriate first step?",
        (
            "Find whether the difference is explained by rounding or a missing component",
            "Delete the row so the table is shorter",
            "Publish the table and ignore the total",
            "Change the total to match a previous year without a note",
        ),
    ),
    _q(
        "dq-l3-a",
        "stat-data-quality",
        3,
        "validation rules",
        "Which record belongs with a quality review of an official table?",
        (
            "The source total, the published total, and any explained difference",
            "The font chosen for the press note",
            "The personal notes of an unrelated office",
            "A draft chart that was never checked",
        ),
    ),
    _q(
        "dq-l4-a",
        "stat-data-quality",
        4,
        "data-quality framework",
        "Which check belongs in a data-quality review of a table proposed for release?",
        (
            "Compare totals with the agreed source and record any unexplained difference",
            "Choose the chart colour preferred by the communication team",
            "Shorten the title so it fits a social-media graphic",
            "Remove footnotes to reduce the length of the release",
        ),
    ),
    _q(
        "dq-l4-b",
        "stat-data-quality",
        4,
        "data-quality framework",
        "A quality framework for a release asks the office to state fitness for use. What must be recorded?",
        (
            "The known limitations that a user needs before relying on the figure",
            "Only the date the file was printed",
            "The preferred colour of the cover page",
            "The number of slides in an internal briefing",
        ),
    ),
)

QUESTION_BY_ID = {item.id: item for item in QUESTIONS}

# Indexes that produce the screening gaps: SDA L2, Survey L2, Data Quality L3.
SCREENING_ANSWER_INDEX: dict[str, int] = {
    "sda-l3-a": 1,
    "sda-l3-b": 1,
    "surv-l3-a": 1,
    "dq-l4-a": 1,
    "dq-l4-b": 1,
}


def public_question(item: DiagnosticQuestion) -> dict:
    return {
        "id": item.id,
        "question": item.prompt,
        "options": list(item.options),
        "competency_id": item.competency_id,
        "competency_name": item.competency_name,
        "domain": item.domain,
        "proficiency_level": f"L{item.level}",
        "topic": item.topic,
    }


def public_assessment() -> dict:
    return {
        "assessment_id": ASSESSMENT_ID,
        "title": ASSESSMENT_TITLE,
        "purpose": "Assess your current competency levels and identify areas requiring targeted development.",
        "question_count": len(QUESTIONS),
        "domains": ["STAT"],
        "questions": [public_question(item) for item in QUESTIONS],
    }
