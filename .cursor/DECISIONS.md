# Decisions

Rules for the Why Not 6 screening demo. Later implementation follows these decisions. This file does not change code.

## D1. The model does not own competency numbers

Competency score, demonstrated level, gap, prerequisite pass or fail, and authorization are computed in the backend from stored keys, stored levels, and the formulas in `ARCHITECTURE.md`.

The model may draft MCQs, read an uploaded document, select or quote retrieved chunks, explain a result it has been given, translate text in a later phase, and assist a learner inside a lesson.

The model may not set a competency score, compute a gap, decide that a prerequisite is met, unlock a pathway item, mark a lesson complete, or publish an MCQ.

Current code that violates this decision stays in the repo until the migration steps run. It is not the scoring authority:

- Client `assessment_score` on node completion
- Default lesson completion score of 85 in `STAT-Learn/frontend/src/lib/api.ts`
- Hardcoded project score 88 in `STAT-Learn/frontend/src/app/projects/page.tsx`
- `node_ready_to_complete` and the ready-keyword heuristic in `STAT-Learn/ai-service/app/services/lesson_chat.py`
- Project mentor defaults `score=0.85` and `passed=True` in `STAT-Learn/ai-service/app/orchestrator/graph.py`
- AI tools that record assessments, evidence, project results, or node completion

## D2. Screening score formula

Each item has one domain, one competency, one level from L1 to L5, and one server-side correct option.

A level is met when at least 60 percent of attempted items at that level are correct and every lower level is met. Demonstrated level is the highest met level. Gap is the non-negative difference between the Statistical Officer required level and the demonstrated level.

Missed item ids are part of the stored explanation. A prose paraphrase is optional and cannot replace the stored numbers.

Diagnostic attempts and published-quiz attempts both call this formula.

## D3. Catalogues are synthetic

iGOT, NSSTA, and TPAC recommendations in the screening demo come from local seed adapters. Each item is labeled synthetic and tagged with its source.

The demo makes no request to a government host. Slides and speech say the adapters are mock now and shaped so a live adapter could replace the seed later. They do not say the live adapter exists.

Seed text is original, written for the demo, and aligned to public category names such as sampling or survey design. It is not copied courseware.

## D4. Publication is a human action

An MCQ becomes visible to a learner only after validation succeeds and the Training Admin approves and publishes it. States are draft, validated, pending_review, approved, published, and rejected.

Validation checks schema and citations in code. The model's suggested answer key is a proposal until the approved record stores the key that scoring will use.

## D5. Retrieval for the demo is single-document and in-process

The screening RAG path extracts one uploaded file, chunks it, and cites chunk ids on each draft. Chunks live in memory or Redis for the session.

PostgreSQL, pgvector, and an object store are the deck's later stack. They are not required to demonstrate source-grounded generation, and they are not introduced for screening.

## D6. Keep the current UI shell

The Next.js App Router, existing component library, and three-service runtime stay. Phase 1 supersedes the visual half of this decision: the authenticated shell is a light institutional interface (navy, slate, teal on white), not the earlier dark career theme. See D12.

## D7. Keep the current runtime for screening

Screening runs on Next.js, FastAPI, the AI service, Redis, and Exasol Personal for accounts when Exasol is available. The existing memory fallback for accounts remains acceptable for a local rehearsal.

Sarvam-105B, GPT-as-fallback, JWT/OIDC, and Parichay are production options from the deck. The screening model path is the provider switch already in `STAT-Learn/ai-service/app/core/llm.py`, including mock mode.

## D8. Demo identities

| Session | Identity | Purpose |
| --- | --- | --- |
| Learner | Arun Kumar, Statistical Officer | Profile, diagnostic, pathway, published quiz |
| Reviewer | Training Admin | Upload, inspect evidence, approve, publish |

The admin is a role label. The demo does not invent a personal name for that account.

Both accounts are seeded before the presentation. The script does not sign up a new user and does not walk the seven-step career onboarding.

## D9. Fail in public with a labeled fallback

If the live model fails, the operator shows a prepared draft that cites real chunks of the uploaded file and says it is the generation fallback. The fallback draft still passes through validation and admin approval. It is not auto-published, and it is not used as a competency score.

## D10. Do not delete career modules to start the demo

Implementation adds the screening path first. Career projects, the workspace runner, unused navigation, and model-writable score tools are removed only after the demo no longer imports them, as listed in `MIGRATION_PLAN.md`.

## D11. Auth on competency writes

When the gap engine and the review queue are built, writes use the session. A request body cannot name a different learner id, submit an official score, or publish an item. The Training Admin role is the only session allowed to approve and publish.

The current unauthenticated assessment, node, and evidence routes are legacy. They are not extended for the new competency records.

## D12. Product name and team name

The product name is STAT-Learn. It is the name on the wordmark, browser title, navigation, sign-in screen, and product description: AI-Powered Competency & Learning Intelligence Platform for India's Official Statistical System.

Why Not 6 is the hackathon team. It appears with SIH team context, such as the sign-in credit line, and is not the product name. The earlier manthaino wordmark is removed from reachable screens. The npm package id `manthaino-frontend` is unchanged because it is not shown in the product.

## D13. Light institutional shell

Phase 1 keeps Tailwind and the existing shadcn-style components. It replaces purple and dark-glass styling with white surfaces, a navy primary, slate text, and a teal secondary. Corner radius is reduced. No chart library was added; domain readiness uses the existing progress bar.

## D14. Demo role is presenter chrome

The backend does not yet expose an admin role. The header session control stores `learner` or `admin` in `sessionStorage` under `statlearn:demo-role`. Learner navigation and admin navigation are never shown together. A learner session that opens `/admin` is returned to `/dashboard`. This switch is not production RBAC. D11 still applies when competency writes are built.

The shell still calls the existing cookie session check. If that call fails, the screens render the typed demonstration profile so the routes can be opened without Exasol.

## D15. Phase 1 did not score

Phase 1 kept diagnostic answers in the browser and showed a fixed profile. Phase 2 replaces that for the diagnostic, gaps, profile, and readiness figures. See D16. Catalogue cards, the pathway illustration, and the assistant prompts remain prepared text. Approval buttons stay disabled.

## D16. Status and priority bands

After the demonstrated level is known:

- Gap 0 is Meets Target, priority Low.
- Gap 1 is Moderate Gap, priority Medium.
- Gap 2 or more is Priority Gap, priority High.

Scored results do not use the Developing label. Below L1 counts as level 0 when subtracting from the target.

## D17. Readiness is the mean of competency scores

A competency score is correct answers divided by the items for that competency in the attempt. Overall readiness, and the overall score on the result page, are the mean of those ratios, displayed as a half-up percentage. Domain readiness is the same mean inside one domain. Competencies with no answers are unassessed and are left out of the mean. They are not filled with the former 72 / 61 / 78 / 84 / 69 figures.

The half-up percentage is for display. The 0.60 level test uses the raw ratio. A level with zero attempts is not met.

## D18. Demo learner header

If the cookie session resolves to a learner, that learner owns the attempt. Otherwise the header `X-Statlearn-Demo-Learner: arun-kumar` maps only to the seeded learner `learner_arun_kumar`. Any other value is rejected. A learner id in the body is ignored. This is a screening shortcut, not production authentication.

## D19. Competency state is memory plus Redis

There is no migration tool in this repository. Attempts and results live in process memory and are snapshotted to Redis when Redis is reachable. They are not written to Exasol. A process restart without Redis drops in-flight attempts.

## D20. Catalogue recommendations

Programmes are synthetic records with a source (iGOT, NSSTA, or TPAC), the competencies they address, a programme level, duration, format, and an optional prerequisite competency level. They are not live government catalogues.

A programme is recommended only when it addresses a stored gap greater than zero and its programme level is above the demonstrated level. The ranker reads the Phase 2 gap record. It does not recompute the score.

Order, first match wins the higher place:

1. Priority Gap before Moderate Gap.
2. Larger gap before smaller gap.
3. Prerequisite met before unmet. A missing prerequisite competency counts as not met. No prerequisite counts as met.
4. Programme level equal to the demonstrated level plus one, before higher levels.
5. Earlier competency in the stored assessment result.
6. Title, then id.

Source is not a ranking factor. The explanation sentence is filled from those fields. The pathway lists the recommended programme, then later programmes for the same competency, then a follow-up assessment that is not completed, then the target level.

## D22. Pathway assessment label

The follow-up assessment step on a pathway is labeled Assessment. It is not a completed activity and it is not a second scored diagnostic. Approved question-bank items stay out of the Phase 2 diagnostic.

## D21. Source-grounded drafts and human publication

The sampling note is a synthetic demo source with section chunks. It is not an official publication. Generation sends those chunk texts to the model and asks for one JSON candidate. If the provider is missing or the output is invalid, nothing is stored and the response is that AI generation is unavailable.

A separate demo-draft action stores a candidate built from the chunk text and labels it Demo-generated draft. It is not labeled AI generated.

A draft needs a question, exactly four non-empty options, a correct option among them, an explanation, a known competency, a level from L1 to L5, and a source chunk that was supplied for the request. An exact normalized duplicate of a draft or approved stem is rejected and not inserted.

Only a request with `X-Statlearn-Demo-Actor: training-admin` can generate, approve, or reject. That header is a screening token, not a government identity. Status can move from DRAFT to APPROVED or DRAFT to REJECTED, and nowhere else. Each transition stores the actor, time, and previous status.

Approved questions appear in the question bank. Drafts and rejected questions do not, and neither enters the Phase 2 diagnostic.
