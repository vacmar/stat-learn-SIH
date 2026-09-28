"""Short study questions for each synthetic catalogue course. The answer index stays on the server."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CourseQuestion:
    id: str
    prompt: str
    options: tuple[str, str, str, str]
    correct_index: int
    lesson: str


def _q(qid: str, prompt: str, options: tuple[str, str, str, str], correct_index: int, lesson: str) -> CourseQuestion:
    if correct_index not in range(4):
        raise ValueError(qid)
    return CourseQuestion(qid, prompt, options, correct_index, lesson)


COURSE_QUESTIONS: dict[str, tuple[CourseQuestion, ...]] = {
    "igot-official-analysis": (
        _q(
            "igot-official-analysis-1",
            "What does the reference period in a statistical table tell the reader?",
            ("The time span the figures describe", "The officer who typed the table", "The colour used in the chart", "The software that stored the file"),
            0,
            "The reference period is the time the numbers describe, such as a month or a year.",
        ),
        _q(
            "igot-official-analysis-2",
            "A total in a published table does not match the sum of its parts. What should you do first?",
            ("Check the notes for rounding or a suppressed cell", "Change the total so the table adds up", "Delete the smallest part", "Publish the table without a total"),
            0,
            "Check the notes before changing a published figure. Rounding or suppression can explain the difference.",
        ),
        _q(
            "igot-official-analysis-3",
            "Why is a classification break shown in an official table?",
            ("So readers can see the groups that make up the total", "So the page has more rows", "So blank cells look complete", "So the title can stay short"),
            0,
            "A classification break shows how a total is split into groups.",
        ),
    ),
    "igot-advanced-analysis": (
        _q(
            "igot-advanced-analysis-1",
            "Two releases of the same series use different base years. What must a reader know before comparing them?",
            ("Whether the series was rebased", "Which font the table uses", "Who approved the colour palette", "How many pages the file has"),
            0,
            "A rebased series is not directly comparable with the older base until the change is explained.",
        ),
        _q(
            "igot-advanced-analysis-2",
            "A sharp one-month movement appears in a seasonally affected series. What is a careful first reading?",
            ("Check whether the movement is seasonal before calling it a new trend", "Treat every rise as a permanent change", "Drop the latest month", "Compare it only with a series from another country"),
            0,
            "Seasonal movement can look like a new trend. Check the seasonal pattern first.",
        ),
        _q(
            "igot-advanced-analysis-3",
            "Why is a revision note attached to an updated official release?",
            ("It tells readers what changed and why", "It replaces the table title", "It hides the earlier figures", "It removes the reference period"),
            0,
            "A revision note says what changed and why, so the earlier release can still be understood.",
        ),
    ),
    "nssta-survey-practicum": (
        _q(
            "nssta-survey-practicum-1",
            "A dwelling is missing from the list used to draw the sample. What is that list called?",
            ("The sampling frame", "The colour legend", "The press note", "The certificate"),
            0,
            "The sampling frame is the list from which the sample is drawn. A missing dwelling is a frame problem.",
        ),
        _q(
            "nssta-survey-practicum-2",
            "An interviewer skips a selected household because nobody is home on the first visit. What keeps the sample intact?",
            ("Follow the revisit rule before replacing the household", "Replace it immediately with a neighbour", "Leave the row blank and continue", "Ask the neighbour to answer for them"),
            0,
            "A selected household is revisited under the survey rule before anyone considers a replacement.",
        ),
        _q(
            "nssta-survey-practicum-3",
            "Why is the same question asked in the same words to every household?",
            ("So the answers can be compared", "So the interview is shorter for every house", "So the form needs no number", "So the respondent can rewrite the question"),
            0,
            "A fixed question wording is what makes answers from different households comparable.",
        ),
    ),
    "tpac-data-quality": (
        _q(
            "tpac-data-quality-1",
            "What does fitness for use mean for a published table?",
            ("The table is good enough for the stated purpose", "The table uses the newest software", "The table has no blank cells at all", "The table was typed twice"),
            0,
            "Fitness for use means the table meets the purpose it is published for, not that every cell is filled.",
        ),
        _q(
            "tpac-data-quality-2",
            "A table is ready for release but one check is still open. What should happen?",
            ("Hold the release until that check is closed", "Publish it and add the check later", "Remove the row that failed", "Change the title so the check no longer applies"),
            0,
            "An open release check means the table is not ready to publish.",
        ),
        _q(
            "tpac-data-quality-3",
            "Which item belongs in a data-quality note for users?",
            ("The known limit of the figures", "The officer's personal phone number", "The colour of the printed copy", "The folder name on a laptop"),
            0,
            "Users need the known limit of the figures, such as coverage or a delayed return.",
        ),
    ),
    "nssta-sampling-note": (
        _q(
            "nssta-sampling-note-1",
            "Why split a survey population into strata before allocating the sample?",
            ("So each important group is represented", "So every form can use a different question", "So the sample can ignore the frame", "So one household can answer for the stratum"),
            0,
            "Strata keep important groups in the sample instead of leaving them to chance.",
        ),
        _q(
            "nssta-sampling-note-2",
            "A stratum has very few units but must still be reported. How should allocation treat it?",
            ("Give it enough sample to support the planned table", "Give it no units because it is small", "Copy answers from a larger stratum", "Drop the stratum from the release without a note"),
            0,
            "A small stratum that will be published needs enough sample, and the note should say if it does not."),
        _q(
            "nssta-sampling-note-3",
            "What is a weight in a sample survey?",
            ("A number that shows how many units one selected unit stands for", "The number of pages in the questionnaire", "The time of day of the interview", "The name of the interviewer"),
            0,
            "A weight says how many units in the population one selected unit represents.",
        ),
    ),
    "igot-sdg": (
        _q(
            "igot-sdg-1",
            "What does disaggregation of an SDG indicator mean?",
            ("Showing the indicator for groups, not only the national total", "Replacing the indicator with a chart colour", "Publishing the indicator with no notes", "Using one number for every district"),
            0,
            "Disaggregation shows the indicator for groups such as sex, age, or place, not only one national total.",
        ),
        _q(
            "igot-sdg-2",
            "A district figure is missing. What should the table do?",
            ("Mark it as not available and say why if known", "Copy the state total into the district cell", "Leave the reader to guess", "Drop the indicator"),
            0,
            "A missing district figure is marked not available. It is not filled with the state total.",
        ),
        _q(
            "igot-sdg-3",
            "Why is the indicator definition printed with the table?",
            ("So readers know exactly what was measured", "So the table can omit the year", "So the source can stay unnamed", "So two different definitions look the same"),
            0,
            "The definition tells the reader what was measured, which keeps later comparisons honest.",
        ),
    ),
    "nssta-reproducible-tables": (
        _q(
            "nssta-reproducible-tables-1",
            "What makes an official table reproducible?",
            ("Another person can follow the documented steps and reach the same figures", "The file is saved on one laptop only", "The table is exported as a picture", "The steps are kept in memory"),
            0,
            "A reproducible table has written steps that another person can follow to the same figures.",
        ),
        _q(
            "nssta-reproducible-tables-2",
            "A formula in the table workbook is changed after the release. What should be kept?",
            ("The earlier file and a note of the change", "Only the newest file, with the old one deleted", "A screenshot and no workbook", "The changed file under the old release date"),
            0,
            "Keep the released file and record the later change. Do not replace the old release silently.",
        ),
        _q(
            "nssta-reproducible-tables-3",
            "Where should the source data for a published table be named?",
            ("In the table notes or the process note", "Only in a private chat", "In the file password", "On a sticky note that is not filed"),
            0,
            "Name the source in the table notes or the process note so the table can be traced.",
        ),
    ),
    "tpac-geospatial": (
        _q(
            "tpac-geospatial-1",
            "A map and a table show the same district total, but the map boundary is newer. What should the note say?",
            ("The map boundary and the table may not match", "The colours are only decorative", "The boundary does not matter", "The table year can be ignored"),
            0,
            "If the map boundary and the table period differ, say so. Readers otherwise treat them as the same area.",
        ),
        _q(
            "tpac-geospatial-2",
            "Why is a small district's point on a map easy to misread?",
            ("The point can hide how small the count is", "The point always means zero", "The point replaces the table", "The point removes the need for a legend"),
            0,
            "A map point can look large even when the count is small. The table and the legend keep the size honest.",
        ),
        _q(
            "tpac-geospatial-3",
            "What belongs in a map legend for a statistical office?",
            ("What the colour or size stands for", "The name of the software licence owner", "The officer's desk number", "The printer model"),
            0,
            "The legend says what colour or size means so the map can be read without guessing.",
        ),
    ),
    "igot-revisions": (
        _q(
            "igot-revisions-1",
            "A published figure is corrected the next month. What should the notice tell users?",
            ("Which figure changed, and the reason", "Only that a new file was uploaded", "The name of the person who found it", "That the old figure was never published"),
            0,
            "A revision notice names the figure that changed and the reason.",
        ),
        _q(
            "igot-revisions-2",
            "Users already quoted the first release. Why must the old figure stay findable?",
            ("So they can see what changed from the number they used", "So the website has two titles", "So the old figure can be deleted later without a record", "So the revision can be denied"),
            0,
            "Keep the earlier figure available so users can see the change from the number they quoted.",
        ),
        _q(
            "igot-revisions-3",
            "Which wording is fit for a public revision note?",
            ("The May total was revised after late returns were added", "Ignore the last release", "The table was wrong and has been replaced quietly", "Do not compare any months"),
            0,
            "Say what was revised and why, in plain language.",
        ),
    ),
    "tpac-coordination": (
        _q(
            "tpac-coordination-1",
            "A training counterpart needs the same table your office will publish next week. What should you share now?",
            ("The planned release date and the current draft status", "The final numbers before the check is done", "A private password to the source system", "Nothing until the next year"),
            0,
            "Share the planned date and the draft status. Do not hand over unchecked final numbers.",
        ),
        _q(
            "tpac-coordination-2",
            "Two offices use different names for the same district. What avoids a mismatched table?",
            ("Agree the name and code before the file is joined", "Let each office keep its own spelling in the joint table", "Drop the district", "Join the files on the officer's name"),
            0,
            "Agree the area name and code before joining files, or the same district can be counted twice.",
        ),
        _q(
            "tpac-coordination-3",
            "A counterpart asks for a figure that has not passed the release check. What is the right reply?",
            ("It is not for use outside the office until the check is closed", "Send it and mark it final", "Send it with no note", "Ask them to estimate it"),
            0,
            "A figure that has not passed the release check is not for use outside the office.",
        ),
    ),
}
