# Phase 2 report

The diagnostic now scores on the server. The browser submits selected options and displays the result. It does not calculate levels. No language model, catalogue ranker, or publication flow was added.

## 1. Backend files changed

- `STAT-Learn/backend/app/services/competency_engine.py` — pure scoring
- `STAT-Learn/backend/app/services/competency_store.py` — attempts in memory, Redis snapshot when reachable
- `STAT-Learn/backend/app/data/diagnostic_seed.py` — diagnostic items and answer keys
- `STAT-Learn/backend/app/api/competency.py` — routes and learner resolution
- `STAT-Learn/backend/app/main.py` — registers the new routers before the older assessment router
- `STAT-Learn/backend/app/core/cache.py` — short Redis connect timeout so a missing Redis does not stall each write
- `STAT-Learn/backend/tests/test_competency_engine.py`

The older `/assessments/start` routes remain for the previous career tests.

## 2. Frontend files changed

- `STAT-Learn/frontend/src/lib/api.ts` — diagnostic, attempt, profile, and gap calls; demo learner header
- `STAT-Learn/frontend/src/app/assessment/page.tsx`
- `STAT-Learn/frontend/src/app/gaps/page.tsx`
- `STAT-Learn/frontend/src/app/competencies/page.tsx`
- `STAT-Learn/frontend/src/app/dashboard/page.tsx`

Pathway, catalogue, and assistant still use the Phase 1 synthetic records. Approve stays disabled.

## 3. Database models and migrations

No Alembic project and no Exasol migration. Attempts are process memory plus a Redis snapshot (`statlearn:competency:attempt:*`). A restart without Redis drops them. Existing tables were not deleted.

## 4. API endpoints

- `GET /assessments/diagnostic`
- `POST /assessments/attempts`
- `GET /assessments/attempts/{attempt_id}` — resume, including saved selections, without the answer key
- `POST /assessments/attempts/{attempt_id}/answers`
- `POST /assessments/attempts/{attempt_id}/complete`
- `GET /assessments/attempts/{attempt_id}/result`
- `GET /competencies`
- `GET /competencies/profile`
- `GET /competencies/gaps`
- `GET /competencies/gaps/{competency_id}`
- `GET /competencies/history`

## 5. Scoring algorithm

Items are grouped by competency and then by level. A level is met only when it has at least one answer and `correct / attempted >= 0.60`, using the raw ratio. Every lower level must also be met. The demonstrated level is the highest level in that chain. No attempts at a level means that level is not met. The correct option is compared on the server.

## 6. L1–L5 mapping

There is no percent-to-level table. Display percentages are half-up and are not fed back into the level test. Unit checks: 59/100 does not meet a level, 60/100 meets it, 61/100 meets it, provided lower levels are already met. If L1 is not met, the level is below L1 and counts as 0 when the gap is subtracted.

## 7. Gap calculation

Gap = max(0, target level − demonstrated level). Targets are Statistical Data Analysis L4, Survey Methodology L3, and Data Quality L4.

- Gap 0: Meets Target, Low
- Gap 1: Moderate Gap, Medium
- Gap 2 or more: Priority Gap, High

Overall readiness is the mean of competency scores in the attempt. Domain readiness is that mean inside the domain.

The screening answer pattern (first option, except the five items named in `DEMO_FLOW.md`) produces:

- Statistical Data Analysis 60%, L2, target L4, gap 2, Priority Gap
- Survey Methodology 67%, L2, target L3, gap 1, Moderate Gap
- Data Quality 60%, L3, target L4, gap 1, Moderate Gap

## 8. Evidence model

Each competency result stores correct, evaluated, and incorrect counts, per-level counts and whether the level was met, correct and incorrect question ids, and the topics of incorrect items. Gap records include `assessment_attempt_id`.

## 9. Session and learner binding

A valid cookie session selects that account's learner. Otherwise only `X-Statlearn-Demo-Learner: arun-kumar` is accepted, and it maps to `learner_arun_kumar`. A learner id in the request body is ignored. This is a screening shortcut, not production authentication.

## 10. Tests performed

`backend/tests/test_competency_engine.py`: 11 passed. Covered threshold boundaries, lower-level gating, status bands, evidence ids, the screening pattern, hidden answer keys, rejected identity, duplicate and invalid answers, a foreign learner, a frozen completed attempt, and result retrieval through profile, gaps, and history.

A live call against FastAPI reproduced the three screening levels above.

## 11. Typechecks and lint

Frontend `tsc --noEmit` passed. ESLint on the changed frontend files passed with no warnings.

## 12. Known limitations

- The diagnostic covers three statistical competencies, not the earlier 18-row static profile. Unassessed domains stay blank.
- Recommended training cards are still the synthetic catalogue, not a ranker.
- Without Redis, attempts die with the backend process. The first snapshot logs a connection error, then later writes stay in memory for that process.
- The demo header is not a substitute for a real official identity.
- Admin approval, MCQ generation, and retrieval are unchanged.

## 13. What Phase 3 should implement

Phase 3 should rank the synthetic iGOT, NSSTA, and TPAC programmes from these gap records: learner, role targets, current level, target level, and prerequisites. It should not recompute scores and should not call a model to decide eligibility. Retrieval, MCQ generation, and human publication stay after that.
