# Screening demonstration flow

A 5–7 minute recording of STAT-Learn for SIH26101. The team is Why Not 6. The product name on screen is STAT-Learn. Catalogues are synthetic. Competency levels come from the answer key and the 60 percent rule. The model does not score, rank, or publish.

## Before recording

1. Start Redis if it is available. If it is not, keep the backend process running for the whole recording. A restart without Redis clears attempts and drafts.
2. Start the backend from `STAT-Learn/backend`: `../.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000`.
3. Start the frontend from `STAT-Learn/frontend`: `npm run dev`.
4. Open the app. Set **Demo session** to Statistical Officer. That shows Arun Kumar. It is a screening control, not a production login.
5. Complete the diagnostic, or rebuild the same result with `PYTHONPATH=. ../.venv/bin/python scripts/prepare_screening_demo.py` from `STAT-Learn/backend`.
6. Confirm the three gaps and the ranked programmes.
7. Switch **Demo session** to Training Admin. Learner navigation leaves. Admin navigation appears.
8. Open Learning Materials. If model generation is unavailable, use **Load demo draft**. The badge must say Demo-generated draft.
9. Approve one draft. Confirm it is in the Question Bank.
10. Switch back to Statistical Officer.

Answer pattern: choose the first option on every item, except these five, where the second option is selected:

- both Statistical Data Analysis items about classification breaks and rebasing
- the Survey Methodology item about dwellings missing from the frame
- both Data Quality items about the release review and fitness for use

That pattern produces Statistical Data Analysis at 60 percent, L2 against L4, gap 2, Priority Gap; Survey Methodology at 67 percent, L2 against L3, gap 1, Moderate Gap; Data Quality at 60 percent, L3 against L4, gap 1, Moderate Gap; overall readiness 62 percent.

## 0:00–0:30 — Dashboard

`/dashboard`

Say that STAT-Learn builds a competency profile for personnel in India's official statistical system. Point at Arun Kumar, Statistical Officer, and the readiness figure returned by the server.

## 0:30–1:45 — Diagnostic

`/assessment`

Title: Statistical Officer Diagnostic. Select the screening answers. Submit assessment. The page does not show the answer key before submit.

## 1:45–2:30 — Result

On the result, read the three competencies, their levels, and the gap labels. Say the demonstrated level is calculated from the answer key using the 60 percent threshold.

## 2:30–3:15 — Gap evidence

`/gaps`

Open Statistical Data Analysis. Expand "Why is this a gap?". Read the level, score, and incorrect question ids. Say the system keeps the evidence behind the gap.

## 3:15–4:00 — Recommendation and pathway

Show the recommended next step on the gap card, then open `/pathway`. The first programme is the L3 iGOT analysis module. The L4 module is next because its prerequisite is not met. The follow-up assessment says it is not completed.

## 4:00–4:40 — Catalogue

`/catalogue`

Show Recommended for Arun Kumar, then the full synthetic catalogue with iGOT, NSSTA, and TPAC. Say these records are not a live government catalogue.

## 4:40–5:50 — Admin materials and draft

Set Demo session to Training Admin. Open `/admin`, then `/admin/materials`. The note is a demo source with Coverage, Stratified sampling, and Allocation.

Open `/admin/mcq-generator`. If the model is configured, Generate MCQs. If it is not, the screen says no draft was created. Load demo draft, and say the badge is Demo-generated draft, not AI generated.

## 5:50–7:00 — Review, approve, question bank

`/admin/mcq-review`

Read the question beside the source chunk. Say the model can propose a question and cannot publish it. Click Approve.

Open `/admin/question-bank`. The approved item is listed. Drafts and rejected items are not. Switch back to Statistical Officer.

Close with: STAT-Learn connects competency assessment, explainable learning recommendations, and governed assessment drafts in one platform.

## What not to claim

Do not claim a live iGOT, NSSTA, or TPAC integration. Do not say the model calculated the level or chose the programme. Do not treat an unapproved draft as part of the diagnostic.
