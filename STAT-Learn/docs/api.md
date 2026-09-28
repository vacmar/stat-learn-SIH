# API (backend FastAPI)

Base URL: `http://localhost:8000` (see `frontend` env `NEXT_PUBLIC_BACKEND_URL`).

## Health

- `GET /health`

## Auth (`/auth`)

- `POST /auth/signup`, `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`

## Learners (`/learners`)

- `GET /learners/me`, `PATCH /learners/me`
- `POST /learners/{learner_id}/skills`, `POST /learners/{learner_id}/evidence`

## Goals (`/goals`)

- `POST /goals/`, `GET /goals/`, `GET /goals/{goal_id}`

## Onboarding (`/onboarding`)

- `GET /onboarding/`, `POST /onboarding/`

## Paths (`/paths`)

- `POST /paths/generate`
- `GET /paths/me/active`
- `GET /paths/{path_id}`
- `POST /paths/{path_id}/regenerate` — body `{ learner_id }`
- `GET /paths/{path_id}/next-node?learner_id=`

## Nodes (`/nodes`)

- `GET /nodes/{node_id}`, `GET /nodes/{node_id}/context`
- `POST /nodes/{node_id}/start`, `GET /nodes/{node_id}/progress`, `GET /nodes/{node_id}/resume`
- `GET /nodes/{node_id}/unlock-conditions?learner_id=`
- `POST /nodes/{node_id}/complete` — body `{ learner_id, assessment_score, practical_pass }`
- `POST /nodes/{node_id}/mistakes`, `GET /nodes/{node_id}/mistakes?learner_id=`

## Assessments (`/assessments`)

- `POST /assessments/start?assessment_id=`
- `POST /assessments/{id}/answer`, `POST /assessments/{id}/finalize`
- `GET /assessments/{id}/result`

## Verification (`/verification`)

- `POST /verification/skills/{skill_id}/start`
- `POST /verification/skills/{skill_id}/submit`
- `GET /verification/skills/{skill_id}/result`

## Projects (`/projects`)

- `GET /projects/{project_id}`
- `POST /projects/{project_id}/submit` — `{ learner_id, artifact }`
- `POST /projects/{project_id}/evaluate` — structured evaluation payload

## Workspace (`/workspace`)

- `POST /workspace/execute` — body `{ code, language?: "python" }`
  - Runs Python on the backend with a short timeout (~4s) and clipped stdout/stderr
  - Demo/local practice pad — not a full isolation sandbox
  - Response: `{ ok, stdout, stderr, exit_code, timed_out, language }`

## Conversations (`/conversations`)

- `GET /conversations/{conversation_id}`
- `POST /conversations/{conversation_id}/messages`

AI service (port 8001): tutor/pathway/mentor chat and `/tools` — see `ai-service/README.md`.
