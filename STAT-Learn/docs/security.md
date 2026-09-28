# Security

## Authentication

- Email/password signup stores hashed credentials; session cookies (`credentials: include`) gate `/paths/me/active` and learner routes.
- CORS is restricted to the frontend origin in development (`http://localhost:3000`).

## Secrets

- Never commit `.env`, password files, or API keys. Use `EXASOL_PASSWORD_FILE` and CI secrets for deploy.
- OpenRouter/Groq keys for AI service belong in environment variables only.

## Data access

- Progression and evidence writes go through backend services, not direct DB access from the browser or LLM.
- Project submissions store artifact URLs/strings; treat learner-supplied links as untrusted (no server-side fetch without sandboxing in production).

## Hardening (production checklist)

- HTTPS everywhere, secure cookie flags, rate limiting on auth and chat endpoints.
- Rotate Exasol and Redis credentials; network isolate database from public ingress.
- Enable dependency scanning in CI and keep Docker base images pinned.
