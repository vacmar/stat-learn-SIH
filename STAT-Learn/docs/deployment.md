# Deployment (summary)

Full judge-facing instructions live in **[RUN_GUIDE.md](./RUN_GUIDE.md)**.

## Local (macOS recommended)

1. **Exasol Personal** — do not use `docker-db` on Apple Silicon:
   ```bash
   exakit start
   ```
2. Credentials (prefer file):
   ```bash
   export EXASOL_PASSWORD_FILE="$HOME/.exasol-starter-kit/credentials/personal_sys_password"
   ```
3. App stack:
   ```bash
   cp .env.example .env   # add HUGGINGFACE_API_KEY
   docker compose up --build
   ```
4. Open http://localhost:3000 — verify:
   - http://localhost:8000/health → `exasol_connected: true`
   - http://localhost:8001/health → LLM `provider`

Backend reaches host Exasol via `EXASOL_DSN=host.docker.internal:8563`.

## Environment highlights

| Variable | Purpose |
|----------|---------|
| `EXASOL_ENABLED` | `false` only for unit tests without DB |
| `EXASOL_DSN` | Host:port for Exasol |
| `EXASOL_PASSWORD_FILE` | Preferred password delivery |
| `REDIS_URL` / Compose Redis | Sessions + path/lesson cache |
| `LLM_PROVIDER` | `huggingface` \| `mock` \| … |
| `NEXT_PUBLIC_BACKEND_URL` | Frontend → backend (bake at image build) |

Optional Linux profile: `docker compose --profile docker-exasol up` (not for Mac Personal workflow).

## CI

- PR: frontend / backend / ai-service CI (lint, types, tests, Docker build)
- `main`: Deploy smoke — compose up + `/health` + frontend curl

See [adr/0001-exasol-personal-on-macos.md](./adr/0001-exasol-personal-on-macos.md).
