# Flaws, Gaps, and Remediation Phases

This report captures product gaps found during local end-to-end runs (onboarding → path → lesson → workspace → projects), plus the runtime work already completed.

Phases **0–11** remain the original Antigravity build contract and can still be executed, merged, or backfilled. Phases **12+** below are the remediation track after the first runnable stack.

---

## Observed flaws (current product)

### Onboarding
- Only three hardcoded target roles; no **Other / custom role** when the user’s goal is not listed.
- Domain text is optional flavor and does **not** drive role selection.
- Skills / interests inputs claim “comma separated” but destroy commas/spaces on every keystroke (array bind + split/trim bug).
- Learning style is free text; product should offer fixed options.
- Weekly available time is a bare number input; needs chips/slider UX.
- Review step leaks internal ids (`role_be`) instead of human titles.

### Path / progression
- Generated nodes show cryptic codes (`C_PY`, `C_SQL`, `PY`, `SQL`) instead of course titles.
- Short demo paths (often ~2 nodes) for beginners; too thin for a real Backend / Data / AI journey.
- Unlocking is incomplete: multiple nodes appear resumable at once (“unlocked everything”).
- Experience level, skills, and weekly time barely reshape path length or order yet.

### Learning / mastery
- **Mark as Mastered** can be clicked without tutor interaction, exercises, or assessment.
- Lesson content is thin; mastery is not gated on concept completion.

### Workspace
- **Shipped (lightweight):** practice pad bound to active path nodes; drafts in localStorage; Python `POST /workspace/execute` with Run + output panel; local self-checks.
- Still not a hardened container sandbox; mastery remains lesson/backend-owned.

### Projects
- Capstone UI accepts a GitHub URL and shows requirement checkboxes.
- Validation/evaluation is thin (stub submit/evaluate); not real repo analysis or CI evidence yet.

### AI
- Tutor/mentor can stream when the AI service is configured, but path generation is still largely rules/mock.
- AI is not the authority for unlock/mastery decisions.

### Runtime (largely addressed in Phase 12)
- Docker `exasol/docker-db` on Apple Silicon often never opens 8563.
- Auth orphan accounts (account without learner), cookie host mismatch (`localhost` vs `127.0.0.1`), Redis host inside Compose.

---

## Proposed phases (remediation track)

```markdown
# phases.md (remediation continuation)

## Phase 12 — Local runtime foundation (SHIPPED / in progress)
What we implemented to make the stack runnable on Mac + Docker Desktop:
- Prefer Exasol Personal (`exakit start`) over `exasol/docker-db` on Apple Silicon
- Compose: Redis + backend + AI + frontend; backend → `host.docker.internal:8563`
- PyExasol auth tables, schema/seed fixes (`role_level`, course coverage, apply.sh)
- Signup/login sessions (Redis), learner repair for orphan accounts
- Cookie/CORS host alignment (`localhost`), frontend env rebuild
- Docs/ADR for personal Exasol; CI soft-fail cleanup; verification stubs

**Exit criteria:** signup → session → `/auth/me` works on http://localhost:3000 with personal Exasol + Compose.

## Phase 13 — Onboarding UX hardening
- Fix skills/interests inputs (free-text or chips; parse on blur/Next only)
- Learning style as selectable options (Visual / Hands-on / Reading / Mixed)
- Weekly time chips or slider (e.g. 5 / 10 / 15 / 20+)
- Role picker: more seeded roles + **Other** with free-text title
- Show human role titles everywhere (never raw `role_be`)
- Persist full onboarding payload; review step mirrors labels

**Exit criteria:** a beginner can complete onboarding without input bugs and see accurate review labels.

## Phase 14 — Path locking & richer curricula
- Replace `C_PY` / `C_SQL` codes with real course titles in UI
- Generate longer role-aware paths from Exasol catalogue (not 2-node stubs only)
- Enforce lock → unlock → in_progress → completed; only one recommended next node
- Use experience, self-reported skills, and weekly time in ranking/length
- Surface lock reasons on dashboard / My Path

**Exit criteria:** beginner Backend path starts with one unlocked node; completing it unlocks the next; failing keeps it locked.

## Phase 15 — Interactive mastery loop
- Remove free **Mark as Mastered**
- Bind lesson → tutor chat → exercises → assessment → mastery
- Require concept coverage / exercise pass before node completion
- Workspace opens the **active node** context (not a blank shell)
- Progress page reflects weak concepts and mastery evidence

**Exit criteria:** Python (or first node) cannot be marked complete without interactive learning evidence.

## Phase 16 — Workspace execution & project validation
- Lightweight `POST /workspace/execute` + Workspace Run UI (**shipped for demo**)
- Hardened container limits / network isolation (still open)
- Wire fuller project evaluation evidence beyond stub submit
- Projects: real submit pipeline, requirement checks, structured evaluate
- Mentor chat grounded on project requirements + submission result
- Evidence written to learner profile on pass

**Exit criteria:** learner can run a snippet safely and pass a project via evaluated submission (not checkbox-only).

## Phase 17 — AI grounding, E2E polish, feature freeze prep
- Path/tutor/mentor tools call Exasol-backed gap/rank APIs
- Integration tests: auth → onboarding → locked path → learn → unlock → project
- UI polish, empty states, error toasts
- Docs/demo script updated for the real loop
- Then enter feature freeze (bugs/tests/perf/demo only)

**Exit criteria:** demo script GOAL → VERIFY → LEARN → UNLOCK → PROJECT runs without mock-only shortcuts.
```

---

## Detailed phase explanations

### Phase 12 — Local runtime foundation (done / continue hardening)

Ship a trustworthy local stack: Exasol Personal on macOS, Compose for app services, persistent auth learners, session cookies that work when the UI is on `localhost:3000`. Keep docker-db as an optional Linux/CI profile only. Document `exakit start` + password file mounting. This phase **absorbs** the former “Exasol integration” and “user registration” intents from the earlier draft once they are actually working end-to-end.

### Phase 13 — Onboarding UX hardening

Fix the forms users hit first. The comma-separated skills/interests bug is a hard blocker. Learning style and weekly time should be constrained choices so pathway logic can consume them. Add **Other** role so goals outside Backend/Data/AI are expressible. Never show internal role ids in review or dashboard.

### Phase 14 — Path locking & richer curricula

Users correctly expect prerequisite unlocking. Short dual-node unlocked paths teach the wrong product story. Pull more courses from the Exasol seed, name them clearly, and gate unlocks through progression services. Experience=Beginner should yield a sensible ordered ladder, not “everything Resume.”

### Phase 15 — Interactive mastery loop

Mastery must be earned. Tie the tutor and lesson concepts to completion rules; disable completion until checks pass. Workspace and lesson views must share the same active `node_id` and conversation context so the AI is teaching the node on the path.

### Phase 16 — Workspace execution & project validation

Make practice and capstones real: sandboxed code execution and a project evaluation pipeline that produces evidence. Checkbox-only project UI is insufficient for DevJam demos.

### Phase 17 — AI grounding & freeze prep

Close the loop so AI explanations and tool calls reflect Exasol analytics and live learner state. Add E2E coverage, then freeze major architecture.

---

## Mapping to earlier draft phases

| Earlier draft | New home |
|---------------|----------|
| Phase 12 Exasol Integration | **Phase 12** (shipped runtime) + remaining Exasol path CRUD in 14/17 |
| Phase 13 User Registration & Auth | **Phase 12** (signup/login/sessions done); harden in 17 tests |
| Phase 14 Workspace Code Execution | **Phase 16** |
| Phase 15 Complete Onboarding & Profile | **Phase 13** (+ profile polish in 17) |
| Phase 16 End-to-End Testing & Polishing | **Phase 17** |

Original Antigravity phases **0–11** stay valid and may be merged/backfilled independently of 12+.

---

## Recommended execution order

1. Finish any leftover Phase 12 hardening (auth edge cases, seed apply on fresh machines).
2. Phase 13 onboarding UX (fast user-visible wins).
3. Phase 14 locking (correct product story).
4. Phase 15 mastery loop.
5. Phase 16 execution/projects.
6. Phase 17 grounding + freeze.
