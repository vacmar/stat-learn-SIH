# manthaino-backend

Backend application for manthaino (FastAPI + Exasol).

This service acts as the authoritative core for learning progression, node state transitions (lock/unlock/complete), and pathway generation using an Exasol data foundation.

## Project Structure

- `app/api/`: FastAPI REST endpoints for the core entities (Goals, Learners, Paths, Nodes, etc.).
- `app/services/`: Business logic governing state machine transitions.
- `app/repository/`: Data access layer (currently mocked for MVP).
- `app/models/`: Pydantic domain models and API payloads.
- `docs/`: Data model and architectural documentation.
- `infra/exasol/`: SQL schema, seeds, and analytical queries.

## Setup & Execution

We recommend using [`uv`](https://github.com/astral-sh/uv) for fast dependency management.

1. **Create a virtual environment:**
   ```bash
   uv venv
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   uv pip install -r requirements.txt
   ```

3. **Run the server locally:**
   ```bash
   uvicorn app.main:app --reload
   ```

   The server will start at `http://127.0.0.1:8000`. 
   - Health check: `http://127.0.0.1:8000/health`
   - Swagger Documentation: `http://127.0.0.1:8000/docs`

## Testing

Run the test suite to verify the state machine behavior:
```bash
PYTHONPATH=. pytest
```