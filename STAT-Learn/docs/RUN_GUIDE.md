# Run guide — manthaino (Exasol Devjam)

Deployment and run instructions for judges and teammates. Target: **Exasol Personal** + Docker Compose on a developer machine (macOS recommended).

---

## What you will run

| Component | How it runs | Port |
|-----------|-------------|------|
| Exasol Personal | Host (`exakit`) | `8563` |
| Redis | Docker Compose | `6379` |
| Backend (FastAPI) | Docker Compose | `8000` |
| AI service | Docker Compose | `8001` |
| Frontend (Next.js) | Docker Compose | `3000` |

Exasol is **mandatory** for the Devjam data platform. On Apple Silicon, do **not** use `exasol/docker-db`.

---

## One-time setup

### 1. Install tools

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Exasol Personal / Exakit (per Exasol Devjam starter kit)
- Git

### 2. Clone

```bash
git clone https://github.com/vacmar/mathaino.git
cd mathaino
```

### 3. Start Exasol Personal

```bash
exakit start
```

Confirm something is listening on port **8563**.

Locate the sys password file from the starter kit (path may vary), e.g.:

```bash
export EXASOL_PASSWORD_FILE="$HOME/.exasol-starter-kit/credentials/personal_sys_password"
# or set EXASOL_PASSWORD in .env (never commit it)
```

### 4. Create `.env`

```bash
cp .env.example .env
```

Minimum for a live AI demo:

```env
LLM_PROVIDER=huggingface
HUGGINGFACE_API_KEY=hf_xxxxxxxx
HUGGINGFACE_MODEL=meta-llama/Llama-3.1-8B-Instruct
EXASOL_ENABLED=true
EXASOL_DSN=host.docker.internal:8563
EXASOL_USER=sys
EXASOL_PASSWORD_FILE=/path/to/personal_sys_password
```

Offline / no HF key (UI + mock paths only):

```env
LLM_PROVIDER=mock
EXASOL_ENABLED=true
```

Compose injects these into `backend` and `ai-service`. Frontend public URLs default to localhost in the image build.

---

## Start the application

```bash
docker compose up --build
```

Wait until containers are healthy, then verify:

```bash
curl -s http://localhost:8000/health
# expect: "status":"ok" and "exasol_connected":true

curl -s http://localhost:8001/health
# expect: "provider":"huggingface" (or "mock")

curl -sf -o /dev/null -w "%{http_code}\n" http://localhost:3000
# expect: 200
```

Open the app: **http://localhost:3000**  
Use **`localhost` consistently** (mixing `127.0.0.1` can break cookies).

---

## First-user walkthrough

1. **Sign up** with email + password.  
2. Complete **7-step onboarding** (try role **Other** → “Android Developer” or “Data Scientist”).  
3. Path generates via AI → **Dashboard**.  
4. Open the active lesson → chat + notes.  
5. Confirm mastery when offered → unlock next node.  
6. Optional: **My Path**, **Progress**, **Projects**.

If the lesson says path missing after a backend rebuild: use **Restore my path** or reload Dashboard (Redis usually restores automatically).

---

## AWS / Azure (optional)

Same Compose stack can run on a Linux VM with Exasol Personal or Exasol SaaS reachable from the backend:

1. Install Docker on the VM.  
2. Point `EXASOL_DSN` at your Exasol endpoint (and TLS options as required).  
3. Open ports `3000` (and optionally `8000`/`8001` for debugging).  
4. Set `NEXT_PUBLIC_BACKEND_URL` / `NEXT_PUBLIC_AI_SERVICE_URL` to the public URLs **before** building the frontend image.

Local Personal Exasol remains the primary Devjam path.

---

## Stopping / resetting

```bash
docker compose down
# keep Redis volume:
# docker compose down -v   # wipes Redis path/session cache
```

Exasol Personal data persists on the host until you reset it via Exakit tools.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `exasol_connected: false` | `exakit start`; check password file; confirm `host.docker.internal` from Docker |
| Login feels slow | Expected — bcrypt + Exasol round-trip; wrong password takes similar time by design |
| Dashboard skeleton forever | Check AI health / HF key; first path gen calls the LLM once |
| Lesson shows raw JSON | Hard-refresh; current build unwraps `message` field |
| Workspace Run fails | Rebuild backend (`docker compose up -d --build backend`); only Python is supported |
| Cookies / “Not authenticated” | Stay on `http://localhost:3000`; don’t mix hosts |
| Apple Silicon + docker-db | Don’t; use Personal only |

---

## Health & smoke (CI equivalent)

```bash
docker compose up -d --build
curl --fail http://localhost:8000/health
curl --fail http://localhost:8001/health
curl --fail http://localhost:3000
# optional practice-pad execute
curl -s -X POST http://localhost:8000/workspace/execute \
  -H 'Content-Type: application/json' \
  -d '{"code":"print(42)","language":"python"}'
```

GitHub Actions `Deploy and Smoke Test` runs this on pushes to `main`.

---

## Security notes for demo

- Never commit `.env` or HF tokens.  
- Rotate any key that appeared in chat logs.  
- Demo accounts are fine on Personal; don’t use production passwords.
