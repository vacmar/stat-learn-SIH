# Migration plan

How the manthaino codebase in `STAT-Learn/` becomes the Why Not 6 screening demo, then what waits until after screening. This phase writes the plan only. Do not delete files, redesign the UI, or rewrite services while following this document.

Order of later work:

1. Add demo seed, the gap engine, and mock catalogues beside the current career data.
2. Retarget existing screens and the assessment API so the demo script in `DEMO_FLOW.md` can be walked.
3. Add the admin MCQ pipeline and restrict the model to drafts.
4. After the screening demo is stable, remove career-only modules that the script does not use.

Nothing in steps 1–3 requires removing the old modules first. Old routes can remain unreachable from the demo nav.

## KEEP

Reuse without changing the product idea they already implement.

| Piece | Path | Why it stays |
| --- | --- | --- |
| Frontend app shell, dark layout, fonts | `STAT-Learn/frontend/src/app/layout.tsx`, `globals.css` | Screening uses this chrome |
| UI primitives | `STAT-Learn/frontend/src/components/ui/` | Buttons, cards, progress, badges |
| Auth forms and cookie client | `STAT-Learn/frontend/src/app/auth/login/page.tsx`, `auth/signup/page.tsx`, `src/lib/api.ts` (`credentials: "include"`) | Session mechanism |
| Logout | `STAT-Learn/frontend/src/components/LogoutButton.tsx` | Session mechanism |
| Notes editor | `STAT-Learn/frontend/src/components/RichNotesEditor.tsx` | Generic, if a lesson stays |
| FastAPI app, CORS, health | `STAT-Learn/backend/app/main.py` | Process shell |
| Cookie session and password hashing | `STAT-Learn/backend/app/api/auth.py` | Auth shell. Drop the demo-only auto-provision (`password == "password"`) before any shared deployment; leave it until that cleanup step |
| Redis client and session TTL pattern | `STAT-Learn/backend/app/core/cache.py` | Demo state cache |
| Answer-key scorer shape | `STAT-Learn/backend/app/services/assessment_scoring.py` `score_answers` | Deterministic scoring pattern. Replace the Python/SQL key; keep comparison-and-count |
| Unlock explanation pattern | `STAT-Learn/backend/app/services/unlock_service.py` `get_lock_explanation`, `check_unlocks` | Structured reason, current versus required |
| Evidence ledger pattern | `record_skill_evidence` in `STAT-Learn/backend/app/repository/state_repo.py` | Idempotent record of a score from a known source |
| LLM provider switch and mock model | `STAT-Learn/ai-service/app/core/llm.py`, `app/core/config.py` | Live model or room fallback |
| HTTP streaming shape | `STAT-Learn/ai-service/app/api/chat.py` | Only if a learning-assistance panel stays |
| Fact-only pathway narration | `explain_pathway_change` in the AI tools | Explains numbers it is given |

## REFACTOR

Same module, new vocabulary and data. Visual layout of existing pages stays.

### Frontend

| Piece | Path | Change when implementation starts |
| --- | --- | --- |
| Sidebar labels and which links the demo shows | `STAT-Learn/frontend/src/components/Sidebar.tsx` | Point the live script at profile, diagnostic, pathway, and admin. Leave workspace and projects in the file. |
| Auth marketing copy | `STAT-Learn/frontend/src/components/AuthShell.tsx` | Replace career and Exasol Devjam lines with the statistical-system product name |
| Onboarding wizard shell | `STAT-Learn/frontend/src/app/onboarding/page.tsx` | Keep the step structure for later. The screening script uses a pre-seeded Arun Kumar and does not depend on a full wizard rewrite |
| Dashboard | `STAT-Learn/frontend/src/app/dashboard/page.tsx` | Show domain levels and gaps instead of a career-goal timeline |
| Pathway | `STAT-Learn/frontend/src/app/path/page.tsx` | Show mock catalogue cards and lock reasons |
| Progress | `STAT-Learn/frontend/src/app/progress/page.tsx` | Show level evidence and missed items |
| Profile | `STAT-Learn/frontend/src/app/profile/page.tsx` | Competency profile. Remove the hardcoded Python / SQL / System Design fallback when the API fails; show an error instead |
| Claimed versus verified panel | `STAT-Learn/frontend/src/components/VerificationDiscrepancyPanel.tsx` | Same comparison layout, L1–L5 labels |
| Lesson | `STAT-Learn/frontend/src/app/lesson/[id]/page.tsx` | Assistance only. Remove "Confirm mastery" as a gate driven by the model |
| Assessment | `STAT-Learn/frontend/src/app/assessment/page.tsx` | Multi-item MCQ. Stop hardcoding `eval_1` and `q_1` |
| API types and calls | `STAT-Learn/frontend/src/lib/api.ts` | Add competency, catalogue, and admin endpoints. Stop defaulting `completeLesson` to score 85 |

### Backend

| Piece | Path | Change when implementation starts |
| --- | --- | --- |
| Learner and skill models | `STAT-Learn/backend/app/models/domain.py` | Domain enum STAT, TECH, GOV, BEH. Proficiency as L1–L5. Role required levels |
| Onboarding catalogue | `STAT-Learn/backend/app/api/onboarding.py` | Statistical Officer and the competency framework instead of software roles |
| Assessment routes | `STAT-Learn/backend/app/api/assessments.py` | Return items, score with the answer key, write levels from the gap engine. Require the logged-in learner |
| Completion | `STAT-Learn/backend/app/services/progression_service.py` `attempt_completion` | Ignore client `assessment_score`. Persist the server score only |
| Verification fusion | `STAT-Learn/backend/app/services/verification_service.py` | Map results onto L1–L5 with the published threshold. Stop treating client floats as authority |
| Ranker | `STAT-Learn/backend/app/services/replanning_service.py` | Rank mock catalogue items with the gap formula in `ARCHITECTURE.md`. The skill-gap term is currently a constant |
| AI HTTP client | `STAT-Learn/backend/app/services/ai_client.py` | Call the model for explanation text and MCQ drafts. Pathway selection stays in the ranker |
| Learners and nodes authorization | `STAT-Learn/backend/app/api/learners.py`, `nodes.py` | Bind writes to the session learner. Today several routes accept a caller-supplied learner id and a caller-supplied score |
| Exasol runtime tables | `STAT-Learn/backend/app/repository/exasol_db.py` | Keep accounts. Screening competency state can stay on Redis. Do not block the demo on the unused catalogue tables in `schema.sql` |

### AI service

| Piece | Path | Change when implementation starts |
| --- | --- | --- |
| Public app | `STAT-Learn/ai-service/app/main.py` | Keep FastAPI. Restrict what the demo mounts |
| Graph | `STAT-Learn/ai-service/app/orchestrator/graph.py` | Keep a tool loop for retrieval and explanation. Remove validator defaults that set `score=0.85` and `passed=True`. Do not bind score-writing tools to the model |
| Prompts | `STAT-Learn/ai-service/app/personas/prompts.py` | Official-statistics context. The prompt already says not to invent scores; the tools must match that sentence |
| Lesson chat | `STAT-Learn/ai-service/app/services/lesson_chat.py` | Drop `node_ready_to_complete` and `_heuristic_ready` as completion signals |
| Context builder | `STAT-Learn/ai-service/app/context/builder.py` | Pass document chunks or lesson text. Do not pass a mastery score for the model to act on |
| Structured models | `STAT-Learn/ai-service/app/models/structured.py` | Add an MCQ draft schema. Remove score and pass fields from any object the demo treats as truth |
| Path generator parsing | `STAT-Learn/ai-service/app/services/path_generator.py` | Model may narrate a stage. Ordering, gaps, and prerequisites stay in the backend |

## REPLACE

New demo data and selection logic take over the job these pieces do now. Leave the old files in the tree until the demo path no longer imports them.

| Piece | Path | Replacement |
| --- | --- | --- |
| Career courses, skills, roles, projects | `STAT-Learn/backend/app/repository/mock_db.py` | Synthetic iGOT, NSSTA, and TPAC seed plus the Statistical Officer required-level profile |
| SQL seed of the same career catalogue | `STAT-Learn/infra/exasol/seed.sql` | Not used by the screening runtime. A later seed matches the mock catalogues if Exasol becomes the catalogue store |
| AI-authored stages materialized as courses | `_materialize_ai_courses`, `_store_ai_capstone`, `_generate_path_from_ai_stages` in `STAT-Learn/backend/app/services/replanning_service.py` | Ranker output over the mock catalogues |
| Goal title fallbacks | `STAT-Learn/backend/app/api/goals.py` | Role competency profile |
| Diagnostic content | `MOCK_ANSWER_KEY` and lesson blob `n1` ("Introduction to Decorators") | Tagged MCQ bank with server keys |
| Career path templates | `_mobile_path`, `_frontend_path`, `_backend_path`, `_data_path`, `_generic_role_path` in `STAT-Learn/ai-service/app/services/path_generator.py` | Not the source of the pathway |
| Static gap tool | `calculate_skill_gaps` and the hardcoded Data Engineer rows in `STAT-Learn/ai-service/app/tools/backend_client.py` | Backend gap engine. The tool may fetch a result; it may not invent one |
| Persona fixture "Alex Mercer / Data Engineer" | same tools module | Arun Kumar fixture, or a fetch of his stored profile |
| Career goal page content | `STAT-Learn/frontend/src/app/goal/page.tsx` | Not on the demo path |
| Dead nav that still says MOCK_API and Llama | `STAT-Learn/frontend/src/components/layout/Navigation.tsx` | Do not mount it. Sidebar remains the shell |
| Standalone tutor with node `n1` | `STAT-Learn/frontend/src/app/chat/page.tsx` | Not on the demo path |
| Browser-side project score | `STAT-Learn/frontend/src/app/projects/page.tsx` | Not on the demo path. The hardcoded score 88 must never be reused for competency |

## REMOVE LATER

Safe to remove only after the screening script no longer depends on them. Do not delete in the documentation phase, and do not delete at the start of implementation.

| Piece | Path | Reason |
| --- | --- | --- |
| Python execute route | `STAT-Learn/backend/app/api/workspace.py` | Unauthenticated local Python. Not a competency assessment |
| Workspace page | `STAT-Learn/frontend/src/app/workspace/page.tsx` | Career practice pad |
| Capstone API and service | `STAT-Learn/backend/app/api/projects.py`, `app/services/project_service.py` | Caller-supplied score; `evaluate_project` also unlocks path `p1` |
| Projects page | `STAT-Learn/frontend/src/app/projects/page.tsx` | Capstone UI |
| Conversation stub summaries | `STAT-Learn/backend/app/api/conversations.py` | Every fifth message is a string stub, not part of the demo |
| Model-callable writes | `record_assessment_result`, `update_skill_evidence`, `evaluate_project`, `complete_learning_node`, `check_unlock_conditions` in `STAT-Learn/ai-service/app/tools/registry.py` | Let the model record scores, pass flags, and unlocks. Offline fallbacks treat the model's values as final |
| Password auto-provision | `login` in `STAT-Learn/backend/app/api/auth.py` | Creates an account when the password is `password` |
| Software role list | `ROLE_CATALOG` in `onboarding.py`, `target_roles` in `mock_db.py` | Career roles |

## Build new, after this documentation phase

These do not exist. They are the screening additions, implemented in a later phase on the architecture in `ARCHITECTURE.md`.

- Gap engine function used by both the diagnostic and the published quiz
- Statistical Officer required-level seed and diagnostic item bank
- Three mock catalogue adapters and the ranker
- Upload, chunk, cite, and draft endpoints
- MCQ state machine and Training Admin review API
- One admin page on the existing layout
- Pre-seeded Arun Kumar and Training Admin
- Mock-provider MCQ draft used by the `DEMO_FLOW.md` fallback

## Explicit non-goals for the first implementation pass

- Replacing Exasol or Redis with PostgreSQL and pgvector
- Sarvam on-prem, Bhashini, Parichay, or any live iGOT or NSSTA client
- Deleting the manthaino modules listed under REMOVE LATER
- A visual redesign of dashboard, path, assessment, profile, or lesson
