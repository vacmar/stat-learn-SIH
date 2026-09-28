# Phase 4 report

A Training Admin can turn the synthetic sampling note into a candidate question, read the source chunk, and approve or reject it. The diagnostic, scoring rule, and recommendation ranker were not changed. Approved questions do not enter the diagnostic.

## 1. Files changed

Backend:

- `STAT-Learn/backend/app/data/sampling_note.py`
- `STAT-Learn/backend/app/services/mcq_generation.py`
- `STAT-Learn/backend/app/services/mcq_store.py`
- `STAT-Learn/backend/app/api/admin_mcq.py`
- `STAT-Learn/backend/app/main.py`
- `STAT-Learn/backend/tests/test_mcq_review.py`

Frontend:

- `STAT-Learn/frontend/src/lib/api.ts`
- `STAT-Learn/frontend/src/app/admin/page.tsx`
- `STAT-Learn/frontend/src/app/admin/materials/page.tsx`
- `STAT-Learn/frontend/src/app/admin/mcq-generator/page.tsx`
- `STAT-Learn/frontend/src/app/admin/mcq-review/page.tsx`
- `STAT-Learn/frontend/src/app/admin/question-bank/page.tsx`

## 2. Source ingestion

The note is stored as one document and three section chunks: Coverage, Stratified sampling, and Allocation. The source label is “Demo source”. Retrieval selects chunks tagged for the requested competency, and falls back to the survey chunks. There is no vector index.

## 3. MCQ schema

A stored question has an id, document id, source chunk ids, question, four options, correct option, explanation, competency, domain, target level, status (`DRAFT`, `APPROVED`, `REJECTED`), origin (`model` or `demo_draft`), timestamps, and the chunk text used as evidence.

## 4. LLM provider

Generation stays in the backend and does not import the scorer or the ranker. When `LLM_PROVIDER` is groq, openrouter, or huggingface and the matching server-side key is present, the service posts the prompt to that provider's chat endpoint. Any failure or missing configuration returns that AI generation is unavailable and stores nothing.

## 5. Prompt and output schema

The prompt includes the document title, chunk ids, section names, and chunk text, plus the competency and target level. The required JSON keys are question, options, correct_option, explanation, and source_chunk_ids.

## 6. Validation

The server rejects a draft unless the question, explanation, and four options are non-empty, the correct option is one of the four, the competency and level are known, and every cited chunk was part of the context sent for that request.

## 7. Duplicate handling

Stems are compared after lowercasing, removing punctuation, and collapsing whitespace. An exact match with an existing draft or approved question returns 409 and is not inserted.

## 8. Review workflow

`GET /admin/mcq-review` lists drafts. Each card shows the badge “AI generated” or “Demo-generated draft”, the options, the correct option, the explanation, and the source chunk text.

## 9. Approval workflow

Approve moves `DRAFT` to `APPROVED`. Reject moves `DRAFT` to `REJECTED`. Any other transition returns 409. Only `X-Statlearn-Demo-Actor: training-admin` is accepted. The learner header is rejected. The header is a screening token, not a government identity.

## 10. Question bank

`GET /admin/question-bank` returns approved questions only, with optional domain and level filters. Drafts and rejected questions stay out. The diagnostic seed is unchanged.

## 11. Audit trail

Each approve or reject stores the question id, action, actor `training-admin`, timestamp, and previous status in process memory.

## 12. API endpoints

- `GET /admin/materials`
- `GET /admin/overview`
- `POST /admin/mcq/generate`
- `POST /admin/mcq/demo-draft`
- `GET /admin/mcq-review`
- `POST /admin/mcq/{id}/approve`
- `POST /admin/mcq/{id}/reject`
- `GET /admin/question-bank`

## 13. Tests

`backend/tests/test_mcq_review.py`: 7 passed. They cover chunks, structural validation, a failed generation that stores nothing, a mocked model draft, duplicates, the demo-draft label, approve, reject, an illegal second transition, bank visibility, a non-admin rejection, and an audit row. The earlier competency tests still pass.

## 14. Typecheck and lint

Frontend `tsc --noEmit` passed. ESLint on the admin pages and `src/lib/api.ts` passed with no warnings.

## 15. Known limitations

- The model call uses a server-side key and stores a draft only when the JSON validates. Otherwise the screen says generation is unavailable.
- Admin authorization is a shared screening header, not production identity.
- Review state is lost if the process restarts without Redis.
- Approved questions are not added to the learner diagnostic.

## 16. What Phase 5 should implement

Phase 5 can offer an optional published-question practice set that uses the same Phase 2 scorer and answer key, still excluding drafts. Live government catalogues, Bhashini, and Parichay stay out of scope.
