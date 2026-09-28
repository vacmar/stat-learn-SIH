# Screening demo scope

This file lists only what the 5–7 minute Smart India Hackathon screening demonstration must show. Production capabilities named in `Why_Not_6.pptx` that are not in this list are out of the screening build. See `DEMO_FLOW.md` for the timed script and `DECISIONS.md` for the rules those features must follow.

The demonstration uses the existing Next.js shell, FastAPI backend, and AI service. It does not redesign screens. It does not claim a live government integration.

## Demo learner

- Name: Arun Kumar
- Role: Statistical Officer
- Profile is pre-seeded so the demo does not spend time on account creation

A second session, **Training Admin**, is pre-seeded for review and publication. The admin is a role, not a named person.

## Required features

### 1. Official / learner competency profile

Show Arun Kumar's profile against the four domains STAT, TECH, GOV, and BEH, with proficiency on L1–L5.

The screen shows, for each assessed competency:

- domain code
- competency name
- required level for Statistical Officer
- demonstrated level
- gap (required minus demonstrated, floored at zero)

Required levels come from a fixed role profile stored as demo seed data.

### 2. Diagnostic MCQ assessment

Arun takes a short diagnostic of pre-seeded multiple-choice items. Each item is tagged with one domain, one competency, and one level. The correct option lives in a server-side answer key.

The learner submits answers. The server scores them. The browser does not send a score.

### 3. Explainable competency-gap identification

After the diagnostic, the product shows a gap per competency and the reason: which items were missed, the pass threshold, and the arithmetic that produced the demonstrated level.

The explanation template is filled with those computed facts. A model may rephrase the same facts for display. It may not change the numbers.

### 4. Personalized learning pathway

From the gaps, a deterministic ranker selects an ordered pathway for Arun. Ranking uses gap size, the item's level relative to the required level, and a prerequisite flag stored on the catalogue item. The screen shows why each item is on the path.

### 5. iGOT, NSSTA, and TPAC recommendations

The pathway draws from three synthetic catalogues: iGOT, NSSTA, and TPAC. Every item is tagged with its source catalogue. The UI states that these catalogues are synthetic demo data.

No network call is made to iGOT, NSSTA, Karmayogi, or any other government API.

### 6. AI-generated MCQs from uploaded learning material

The Training Admin uploads one short document (a synthetic PDF or text note prepared for the demo). The pipeline extracts text, splits it into chunks, and asks the model to draft MCQs grounded in those chunks.

The model output is a draft. It includes a proposed stem, options, the model's suggested key, and the chunk ids it used. It does not become a scored assessment and it does not change Arun's competency profile.

### 7. Source-grounded generation

For each drafted item, the admin view shows the source chunk text that the draft cites. The draft is rejected by validation when a cited chunk id is missing or the cited text is empty. Screening retrieval is in-process chunk lookup over the uploaded document, not a new vector database.

### 8. Human admin review and approval

Drafted items enter a review queue with states: draft, validated, pending_review, approved, published. Schema checks (required fields, one correct option, a real citation) run in application code before the admin acts.

Only the Training Admin can approve. Approval is an explicit action. The model cannot publish.

### 9. Published assessment returns to the learner

After approval, Arun sees the published quiz, takes it, and receives a score from the same answer-key scorer used for the diagnostic. The result can update the displayed competency only through that scorer.

## Demo seed that must exist before the room

- Arun Kumar, Statistical Officer, with a required-level vector across a small competency set in STAT, TECH, GOV, and BEH
- A diagnostic item bank with answer keys, covering at least one clear gap the presenter can land by answering selected items incorrectly
- Synthetic catalogue rows for iGOT, NSSTA, and TPAC, each tagged with domain, level, prerequisites, and source
- One short upload document whose text can support two or three MCQs
- Training Admin session
- A working model provider or the mock provider, so generation still returns a valid draft if the live model fails

## Excluded from this demonstration

These items appear in the pitch deck or the full problem statement. They are not part of the screening build:

- Live iGOT, NSSTA, or TPAC API integration, enrolment, or completion sync
- PostgreSQL, pgvector, S3/MinIO, Sarvam on-prem, Parichay or other SSO, and Bhashini translation UI
- Competency decay, organization-wide heatmaps, and predictive workforce analytics
- Multilingual MCQ generation
- The existing career capstone, Python workspace, and free-text career-goal picker as part of the story
- Production deletion of old manthaino modules
