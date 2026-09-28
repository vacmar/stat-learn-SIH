# manthaino-ai-service

LangGraph orchestrator: tutor, pathway reasoning, project mentor; tools call the backend API.

## Path generation

`POST /path/generate` — author a tailored pathway + capstone from a learner profile.

Body fields: `target_role`, `target_role_id`, `target_domain`, `known_skills`, `interests`, `experience_level`, `learning_style`, `weekly_time`, `goals`.

Returns `PathwayExplanation` (`stages`, `summary`, `capstone`, …). Uses the configured LLM (`LLM_PROVIDER=openrouter|groq|mock`); falls back to a profile-aware mock when the provider is `mock` or the LLM call fails.

The backend calls this endpoint during onboarding and materializes locked path nodes from the returned stages.

## Setup

```bash
cd ai-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Environment

| Variable | Purpose |
|----------|---------|
| `BACKEND_URL` | Backend base URL (default `http://localhost:8000`) |
| `REDIS_URL` | Optional cache |
| `OPENROUTER_API_KEY` / Groq keys | Live LLM (mock model used when unset) |

## Development

```bash
PYTHONPATH=. uvicorn app.main:app --reload --port 8001
```

## Test

```bash
PYTHONPATH=. pytest -v
ruff check .
```
