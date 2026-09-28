# Architecture

manthaino is a monorepo with three runtime services and an Exasol-backed data layer.

## Components

| Layer | Location | Role |
|-------|----------|------|
| Frontend | `frontend/` | Next.js App Router UI: onboarding, path, lesson, workspace practice pad, progress, projects |
| Backend | `backend/` | FastAPI state machine: paths, nodes, assessments, verification, projects |
| AI service | `ai-service/` | LangGraph orchestrator, tutor/pathway/mentor personas, tool calls to backend |
| Data | `backend/infra/exasol/` | Schema, seeds, analytical queries (Exasol Personal locally) |

## Request flow

1. Browser talks to **backend** for authoritative learner/path/progression state (session cookies).
2. Browser talks to **ai-service** for streaming tutor and structured agent responses; tools read/write via backend APIs.
3. **Redis** caches ephemeral assessment sessions; durable results land in Exasol / in-memory repo for tests.

## Design principles

- LLMs do not write progression tables directly; they submit evidence/evaluations; backend services apply rules.
- Path generation and replanning use skill gaps, prerequisites, and preserved completed nodes.
- Unlock logic is deterministic (`unlock_service`) and exposed to the UI via `/nodes/{id}/unlock-conditions`.

See [product-flow.md](./product-flow.md) and [data-model.md](./data-model.md).
