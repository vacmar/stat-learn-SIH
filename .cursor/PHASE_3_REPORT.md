# Phase 3 report

Training recommendations now follow the Phase 2 gap records. The scoring engine was not changed, and no language model ranks or writes the reasons.

## 1. Backend files changed

- `STAT-Learn/backend/app/data/catalogue_seed.py` — synthetic catalogue
- `STAT-Learn/backend/app/services/recommendation_engine.py` — ranker and pathway sequence
- `STAT-Learn/backend/app/api/competency.py` — three read endpoints
- `STAT-Learn/backend/tests/test_recommendations.py`

## 2. Frontend files changed

- `STAT-Learn/frontend/src/lib/api.ts`
- `STAT-Learn/frontend/src/app/dashboard/page.tsx`
- `STAT-Learn/frontend/src/app/gaps/page.tsx`
- `STAT-Learn/frontend/src/app/competencies/page.tsx`
- `STAT-Learn/frontend/src/app/pathway/page.tsx`
- `STAT-Learn/frontend/src/app/catalogue/page.tsx`

The Phase 1 file `frontend/src/demo/catalog.ts` remains for the assistant prompts. The dashboard, pathway, and catalogue no longer treat it as the recommendation source. Admin approval is still disabled.

## 3. Catalogue schema

Each programme has an id, title, source, description, one or more competencies, a programme level, duration, format, and an optional prerequisite (competency id and minimum level). Every row is marked synthetic. The seed keeps the earlier titles and adds an L4 iGOT analysis module whose prerequisite is Statistical Data Analysis at L3.

## 4. Recommendation algorithm

The service loads the latest completed attempt and passes its competency rows to `rank_programmes`. It does not call `score_attempt`. A programme is eligible when it addresses a gap greater than zero and its level is above the demonstrated level.

## 5. Ranking rules

1. Priority Gap before Moderate Gap.
2. Larger gap before smaller gap.
3. Prerequisite met before unmet.
4. Programme level equal to demonstrated level + 1 before higher levels.
5. Earlier competency in the stored result.
6. Title, then id.

Source is not a ranking factor.

## 6. Prerequisite handling

No prerequisite is treated as met. Otherwise the learner's demonstrated level for that competency must be at least the minimum. If that competency was not assessed, the prerequisite is not met. An unmet prerequisite sorts the programme after one that is ready, for the same gap.

## 7. Pathway generation

Journeys follow the ranked competency order. Each journey is Current, then the first programme as Recommended, later programmes as Next, then a follow-up assessment marked not completed, then Target. No step is marked completed.

## 8. API endpoints

- `GET /competencies/recommendations`
- `GET /competencies/pathway`
- `GET /competencies/catalogue`

The learner comes from the Phase 2 cookie or `X-Statlearn-Demo-Learner` header. A learner id in the query string is ignored. With no completed attempt the message tells the learner to complete the diagnostic. If every assessed competency meets its target, the message says so and the recommendation list is empty. The catalogue endpoint still returns every synthetic programme.

## 9. Example for Arun Kumar

Using the screening gaps (Statistical Data Analysis L2→L4 gap 2, Survey Methodology L2→L3 gap 1, Data Quality L3→L4 gap 1), the order is:

1. Analysis of official statistical datasets (iGOT, L3, prerequisite met)
2. Advanced interpretation of official releases (iGOT, L4, prerequisite not met)
3. Survey methodology practicum (NSSTA, L3, prerequisite met)
4. Data quality frameworks for published tables (TPAC, L4, prerequisite met)

Sampling, SDG, computing, geospatial, communication, and coordination programmes stay in the catalogue and are not recommended, because those competencies were not in the diagnostic gaps.

The first reason is: "Addresses Statistical Data Analysis, where your demonstrated level is L2 against a target of L4."

## 10. Tests performed

`backend/tests/test_recommendations.py`: 14 passed. They cover eligibility, exclusion, gap size, priority, level suitability, prerequisite met and unmet, meets-target suppression, stable ordering, explanation text, the screening seed order, no score recomputation, no model import, session binding, the empty-attempt message, and the synthetic catalogue list.

## 11. Typecheck and lint

Frontend `tsc --noEmit` passed. ESLint on the changed pages and `src/lib/api.ts` passed with no warnings.

## 12. Known limitations

- The assistant page still quotes the older static programme sentences.
- Pathway and catalogue cards are not a record of training already completed.
- Recommendations disappear if the backend process restarts and Redis has no attempt snapshot.
- Ranking covers only the synthetic seed. It is not a live iGOT, NSSTA, or TPAC integration.

## 13. What Phase 4 should implement

Phase 4 can add source-grounded MCQ drafts from an uploaded document, still without letting the model set a score or publish an item. Human approval stays a separate step. Live government catalogues stay out of scope until an authorized adapter exists.
