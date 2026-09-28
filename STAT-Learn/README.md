# manthaino

**Adaptive AI learning on Exasol Personal (Local)** — onboard any career role, generate an AI learning path, teach node-by-node with a live tutor. The **backend** owns unlocks and mastery; the LLM only teaches.

**Devjam deployment:** Exasol Personal → **Local** (`exakit` on your machine + Docker Compose for the app).

**Team:** Why Not · **Track:** AI Agents That Get Things Done

---

## Table of contents

- [Project overview](#project-overview)
- [Demo video & pitch deck](#demo-video--pitch-deck)
- [Setup instructions](#setup-instructions)
- [Usage instructions](#usage-instructions)
- [Stop / restart / rebuild](#stop--restart--rebuild)
- [Troubleshooting](#troubleshooting)
- [More documentation](#more-documentation)

---

## Project overview

manthaino is an adaptive learning platform built for **Exasol Devjam**. A learner picks any target role (catalog or free-text **Other**), completes a short onboarding profile, and receives a **personalized, dependency-aware path**. Each unlocked node opens a **focus lesson** (ChatGPT-style tutor + rich notes). When the tutor judges mastery, the learner confirms — the **backend** unlocks the next node and updates Progress. The LLM cannot invent unlocks or scores.

### What it does

| Step | Behavior |
|------|----------|
| Auth | Sign up / log in (HTTP-only cookies). Accounts & learners stored in **Exasol Personal**. |
| Onboarding | 7 answers: name, role, domain, experience, skills, interests, learning style + weekly time. |
| AI path | Backend calls AI `POST /path/generate` → stages + capstone → first node **unlocked**, rest **locked**. |
| Learn | Focus UI (sidebar hidden): lesson chat scoped to the current node + rich notes. |
| Practice | **Workspace** practice pad: path-node drafts, Python **Run** → stdout/stderr, local self-checks. |
| Mastery | AI-gated confirm → sequential unlock; Progress / My Path update. |
| Projects | Capstone recommended from the AI path (role-aligned). |

### Stack

| Layer | Technology | Port |
|-------|------------|------|
| Frontend | Next.js 16, TypeScript, Tailwind | `3000` |
| Backend | FastAPI (auth, paths, nodes, lessons, projects) | `8000` |
| AI service | LangChain + Hugging Face Inference | `8001` |
| Cache | Redis (sessions, path/lesson cache) | `6379` |
| Data platform | **Exasol Personal** (Local) | `8563` |

### Architecture

```text
Browser :3000
  ├─► Backend :8000 ──► Exasol Personal :8563 (host)
  │         ├─────────► Redis :6379
  │         └─────────► AI :8001   (path generate)
  └─► AI :8001                     (lesson chat → Hugging Face)
```

### Repository layout

```text
mathaino/                 ← run all docker compose commands from here
├── frontend/
├── backend/
├── ai-service/
├── docs/
├── docker-compose.yml
├── .env.example
└── README.md
```

### Known limits

- Multi-track “Duolingo” role switcher: designed, not fully shipped in this window.
- Workspace **Run** is a lightweight backend Python execute (timeout + output caps) — not a full hardened sandbox.
- Full auto project eval / repo CI evidence: not in this cut.
- Paths are Redis-cached for fast restore; Exasol holds accounts (+ lesson sessions when connected).

---

## Demo video & pitch deck

| Asset | Link |
|-------|------|
| **Demo video** | [Google Drive folder](https://drive.google.com/drive/folders/1gJi4xPHb1ambAe_zFNwnwIV2xQTDvYt1?usp=sharing) |
| **Pitch deck** | [Google Drive folder](https://drive.google.com/drive/folders/1gJi4xPHb1ambAe_zFNwnwIV2xQTDvYt1?usp=sharing) |

---

## Setup instructions

Follow **A → G in order**. Do not skip Exasol on macOS.

### A. Prerequisites

| Tool | Why |
|------|-----|
| **Git** | Clone the repo |
| **Docker Desktop** | Redis, backend, AI service, frontend |
| **Exasol Personal / Exakit** | Mandatory data platform (`exakit start`) |
| **Hugging Face token** | Live AI (or set `LLM_PROVIDER=mock`) |

**Ports that must be free:** `3000`, `8000`, `8001`, `6379`, `8563`.

**macOS:** Do **not** use `exasol/docker-db` on Apple Silicon — use **Exasol Personal** only.

```bash
docker version
docker compose version
```

### B. Clone the repo (path matters)

```bash
git clone https://github.com/vacmar/mathaino.git
cd mathaino
```

Confirm you are in the folder that contains `docker-compose.yml`:

```bash
pwd
ls
# expect: docker-compose.yml  frontend  backend  ai-service  docs  README.md  .env.example
```

Example absolute path:

```text
/Users/vaaheesan/manthaino/mathaino
```

**Always run `docker compose` from this directory.**

### C. Start Exasol Personal (Local)

Exasol runs on the **host**, not in the default Compose stack.

```bash
exakit start
```

Confirm port **8563**:

```bash
lsof -iTCP:8563 -sTCP:LISTEN || true
nc -vz 127.0.0.1 8563
```

Background: [docs/adr/0001-exasol-personal-on-macos.md](./docs/adr/0001-exasol-personal-on-macos.md).

### D. Create `.env`

```bash
cp .env.example .env
open -e .env    # or: nano .env
```

**Live AI demo** — put your key in `.env`:

```env
LLM_PROVIDER=huggingface
HUGGINGFACE_API_KEY=hf_your_token_here
HUGGINGFACE_MODEL=meta-llama/Llama-3.1-8B-Instruct

EXASOL_ENABLED=true
EXASOL_DSN=host.docker.internal:8563
EXASOL_USER=sys
EXASOL_SCHEMA=MANTHAINO
```

**No HF key** (mock AI):

```env
LLM_PROVIDER=mock
EXASOL_ENABLED=true
EXASOL_DSN=host.docker.internal:8563
EXASOL_USER=sys
EXASOL_SCHEMA=MANTHAINO
```

| Variable | Required | Meaning |
|----------|----------|---------|
| `LLM_PROVIDER` | Yes | `huggingface` or `mock` |
| `HUGGINGFACE_API_KEY` | If using HF | Inference token |
| `HUGGINGFACE_MODEL` | Recommended | Default Llama 3.1 8B Instruct |
| `EXASOL_ENABLED` | Yes | `true` for Local Personal |
| `EXASOL_DSN` | Yes | Docker → host: `host.docker.internal:8563` |
| `EXASOL_USER` | Yes | Usually `sys` |
| `EXASOL_SCHEMA` | Yes | `MANTHAINO` |

Never commit `.env` (gitignored).

### E. Confirm the Exasol password file

Compose mounts:

```text
$HOME/.exasol-starter-kit/credentials/personal_sys_password
  →  /run/secrets/exasol_sys_password   (inside backend container)
```

```bash
ls -la "$HOME/.exasol-starter-kit/credentials/personal_sys_password"
```

If missing: symlink your real Exakit password file to that path, edit the `backend.volumes` line in `docker-compose.yml`, or set `EXASOL_PASSWORD=...` in `.env` (do not commit).

### F. Start the stack with Docker

```bash
pwd
# must show .../mathaino (folder with docker-compose.yml)

docker compose down
docker compose up --build -d
```

| Service | Role | URL |
|---------|------|-----|
| `redis` | Sessions + path/lesson cache | `localhost:6379` |
| `ai-service` | Path generate + lesson tutor | http://localhost:8001 |
| `backend` | API + Exasol + Redis | http://localhost:8000 |
| `frontend` | Learner UI | http://localhost:3000 |

```bash
docker compose ps
docker compose logs -f --tail=100
# Ctrl+C stops following logs only
```

First build may take several minutes.

### G. Verify setup

```bash
docker compose ps

curl -s http://localhost:8000/health
# expect: "status":"ok", "exasol_connected":true

curl -s http://localhost:8001/health
# expect: "provider":"huggingface" (or "mock")

curl -sf -o /dev/null -w "frontend_http=%{http_code}\n" http://localhost:3000
# expect: frontend_http=200
```

Open: **http://localhost:3000**  
Use **`localhost`**, not `127.0.0.1` (auth cookies).

### Quick copy-paste (after tools are installed)

```bash
git clone https://github.com/vacmar/mathaino.git
cd mathaino

exakit start
ls -la "$HOME/.exasol-starter-kit/credentials/personal_sys_password"

cp .env.example .env
# edit .env → HUGGINGFACE_API_KEY=...

docker compose up --build -d

curl -s http://localhost:8000/health
curl -s http://localhost:8001/health
open http://localhost:3000
```

---

## Usage instructions

Once setup verification passes:

1. Open **http://localhost:3000**.
2. Click **Sign up** (email + password). Prefer a fresh account for demos.
3. Complete **onboarding** (7 steps). Use role **Other** for any custom title (e.g. Android Developer, Data Scientist).
4. Wait for **AI path generation**, then land on the **Dashboard**.
5. Open the **active** (unlocked) node → focus lesson:
   - Chat with the AI tutor (scoped to this node).
   - Take **rich notes** (title, bold, lists, tables) and Save.
6. Optional — **Workspace**: draft Python for the current node, click **Run**, inspect stdout/stderr. Mastery still happens in the lesson.
7. When the tutor marks the node ready, click **Confirm mastery**.
8. Confirm the **next node unlocks**; check **My Path**, **Progress**, and **Projects** (AI capstone).

**Tips**

- Only one node is unlocked at a time until mastery is confirmed.
- After a backend rebuild, reload Dashboard (Redis usually restores the path) or use **Restore my path** on the lesson screen.
- Wrong password shows a plain message (not raw JSON).
- Workspace drafts save in the browser (`localStorage`); Reset restores the starter template.
---

## Stop / restart / rebuild

```bash
docker compose stop          # pause
docker compose start         # resume
docker compose down          # stop containers
docker compose up --build -d # rebuild after code/.env changes

# wipe Redis volumes (clears cached paths/sessions)
docker compose down -v
docker compose up --build -d
```

Exasol Personal data stays on the host until you reset it with Exakit.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `no configuration file provided` | `cd` to the directory that contains `docker-compose.yml` |
| `exasol_connected: false` | `exakit start` → `nc -vz 127.0.0.1 8563` → check password file → `docker compose logs backend` |
| Password file missing | Fix path under `$HOME/.exasol-starter-kit/credentials/` or set `EXASOL_PASSWORD` in `.env` |
| Login / session issues | Use only `http://localhost:3000` |
| Dashboard loading forever | Check AI health + HF key; first path gen calls the LLM |
| Port in use | Free 3000 / 8000 / 8001 / 6379 / 8563 |
| Path gone after rebuild | Reload Dashboard or **Restore my path** |

```bash
docker compose logs backend --tail=200
docker compose logs ai-service --tail=200
```

---

## More documentation

| Doc | Path |
|-----|------|
| Extra run detail | [docs/RUN_GUIDE.md](./docs/RUN_GUIDE.md) |
| Architecture / API | [docs/](./docs/) |

Optional local tests:

```bash
cd backend && EXASOL_ENABLED=false pytest -q
cd ../ai-service && LLM_PROVIDER=mock pytest -q
cd ../frontend && npm ci && npm run lint && npx tsc --noEmit && npm run build
```

**Submission form:** Exasol Personal — **Local**.
