# Phase 1 report

STAT-Learn now has an institutional frontend shell. Competency scoring, recommendations, retrieval, and admin approval remain later phases. The backend and AI service were not modified.

## 1. Files changed

New frontend files:

- `STAT-Learn/frontend/src/components/AppShell.tsx`
- `STAT-Learn/frontend/src/demo/types.ts`
- `STAT-Learn/frontend/src/demo/role.ts`
- `STAT-Learn/frontend/src/demo/learner.ts`
- `STAT-Learn/frontend/src/demo/competencies.ts`
- `STAT-Learn/frontend/src/demo/catalog.ts`
- `STAT-Learn/frontend/src/demo/assessments.ts`
- `STAT-Learn/frontend/src/demo/pathway.ts`
- Learner routes under `src/app/competencies`, `gaps`, `pathway`, `catalogue`, and `assistant`
- Admin routes under `src/app/admin`, `admin/materials`, `admin/mcq-generator`, `admin/mcq-review`, and `admin/question-bank`

Updated frontend files:

- `src/app/globals.css`, `src/app/layout.tsx`, `src/app/page.tsx`
- `src/app/dashboard/page.tsx`, `src/app/assessment/page.tsx`
- `src/components/Sidebar.tsx`, `AuthShell.tsx`, `LogoutButton.tsx`
- `src/components/layout/Navigation.tsx` (brand strings only; the component is still unused)
- `src/app/auth/login/page.tsx`, `src/app/auth/signup/page.tsx`
- Legacy routes replaced with redirects: `path`, `profile`, `progress`, `workspace`, `projects`, `goal`, `chat`, `onboarding`, `lesson/[id]`

Documentation:

- `.cursor/DECISIONS.md` (D6 visual portion superseded; D12–D15 added)
- `.cursor/DEMO_FLOW.md` rewritten to the Phase 1 routes
- `.cursor/PHASE_1_REPORT.md` (this file)

## 2. Routes created or changed

Learner: `/dashboard`, `/competencies`, `/assessment`, `/gaps`, `/pathway`, `/catalogue`, `/assistant`.

Admin, shown only for the Training Admin session: `/admin`, `/admin/materials`, `/admin/mcq-generator`, `/admin/mcq-review`, `/admin/question-bank`.

`/` now opens `/dashboard`. Sign-in and sign-up return to `/dashboard`. Old career routes redirect as recorded in `DEMO_FLOW.md`.

## 3. Old product concepts removed from the reachable product

The manthaino wordmark, "LEARN on ur phase", the career onboarding entry, the software pathway, workspace, capstone projects, and the standalone tutor are no longer reachable screens. Those route files now redirect. Career copy was not left on the sign-in, dashboard, assessment, or navigation that the shell mounts.

Unused components that still mention older ideas, such as `VerificationDiscrepancyPanel.tsx`, are not mounted.

## 4. STAT-Learn branding changes

Browser title and metadata are STAT-Learn. The wordmark is STAT-Learn in the header, sidebar, and sign-in panel. The product line is "AI-Powered Competency & Learning Intelligence Platform for India's Official Statistical System." Why Not 6 appears only as the team credit on the sign-in panel, with SIH26101. The package name `manthaino-frontend` was left as an internal id. No favicon file existed to retitle.

## 5. New product concepts introduced

Competency domains STAT, TECH, GOV, and BEH. Levels L1–L5. Statuses Meets Target, Developing, Moderate Gap, and Priority Gap. A diagnostic assessment shell. Gap explanations. A competency pathway through synthetic iGOT, NSSTA, and TPAC programmes. A contextual assistant that reads the prepared profile. An administration area for materials, generation, review, and the question bank.

## 6. Demo data created

Typed modules in `STAT-Learn/frontend/src/demo/` hold one coherent profile for Arun Kumar, Statistical Officer: 72% readiness, 18 competencies, three priority gaps (Statistical Data Analysis L2 to L4, Survey Methodology L2 to L3, Data Quality L3 to L4), domain readiness STAT 61%, TECH 78%, GOV 84%, BEH 69%, nine synthetic programmes, eight diagnostic items, and two review drafts tied to a synthetic sampling note. The assistant answers are stored strings. Nothing is fetched from a government API.

## 7. Tests and typechecks performed

From `STAT-Learn/frontend`:

- `./node_modules/.bin/tsc --noEmit` passed
- `./node_modules/.bin/eslint . --max-warnings 0` passed

The existing `next dev` server on port 3000 returned HTTP 200 for every new learner and admin route and HTTP 307 for `/path`, `/projects`, and `/onboarding`. In the browser: dashboard metrics and pathway steps, diagnostic start and answer selection, gap explanation, catalogue filter from 9 programmes to 3 iGOT records, assistant copy, admin overview counts, disabled Approve on review, session switch from Statistical Officer to Training Admin and back to `/dashboard`, and the sign-in screen with the STAT-Learn wordmark and team credit.

## 8. Known issues

- The session control is `sessionStorage` presenter chrome, not a backend role.
- Diagnostic completion does not score and does not update the profile.
- MCQ generator does not upload or call a model. Approve stays disabled.
- The assistant does not call the AI service.
- `Navigation.tsx` is still unused and is not in the live shell.
- The backend still contains the career APIs. They are not what these screens call.
- Legacy redirect files no longer contain the old page implementations. They remain as routes so old URLs do not 404.

## 9. What Phase 2 should implement

Phase 2 should implement the deterministic competency engine on the backend: answer-key scoring, the L1–L5 threshold rule, gap records that cite missed items, and session-bound writes. It should not let the model set a score. The diagnostic completion view and the profile should then read those results instead of only the fixed demonstration file. Recommendation ranking over the synthetic catalogues can follow the same engine. Retrieval, admin publication, and live catalogue adapters stay later than that engine.
