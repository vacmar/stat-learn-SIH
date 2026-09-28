# STAT-Learn

AI-powered competency and learning intelligence for India's Official Statistical System.

STAT-Learn shows a statistical officer where they stand, what to improve, and which public [iGOT Karmayogi](https://igotkarmayogi.gov.in/#/) courses to study next. Scores and gaps are calculated in the backend. A language model may draft quiz questions; it does not set levels, rank courses, or publish them.

**Team:** Why Not 6 · **Team ID:** 176881 · **Problem:** SIH26101 · **Ministry:** Ministry of Statistics and Programme Implementation · **Theme:** Smart Education

Why Not 6 is the team name. The product name is STAT-Learn.

## What an officer can do

1. Register with centre or state, ministry or department, organisation, and designation. Those details are stored and shown on **My account**.
2. Sign in. The home page stays on the sign-in screen until the account is authenticated.
3. Take the Statistical Officer diagnostic. The backend scores it and records the level for each skill.
4. Read the gaps, the pathway, and the certificates. A certificate appears when the demonstrated level matches the goal.
5. Open **Courses**. The list is the public iGOT catalogue. Study a course here and finish it by answering its questions. **Open on iGOT** goes to the same course on the iGOT portal. Completing a course here does not change the officer's iGOT transcript.
6. Training admins can review drafted MCQs before anything is published.

Domains used in the profile are Statistical (STAT), Technical (TECH), Digital governance (GOV), and Behavioural (BEH). Proficiency runs from L1 to L5.

## Stack

| Layer | Technology | Port |
| --- | --- | --- |
| Frontend | Next.js, TypeScript, Tailwind | 3000 |
| Backend | FastAPI | 8000 |
| Accounts and course progress | SQLite (`backend/data/statlearn.sqlite`) | local file |
| Sessions | Redis | 6379 |
| AI service | Optional. Drafts MCQs only | 8001 |

Accounts are not stored in Exasol for this build. Leave `EXASOL_ENABLED=false`.

## Run it locally

From this `STAT-Learn` folder.

```bash
docker compose up -d redis
cd frontend && npm install && npm run dev
```

In another terminal:

```bash
cd backend
../.venv/bin/uvicorn app.main:app --host :: --port 8000
```

Create the virtual environment first if it is missing:

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
```

Open [http://localhost:3000](http://localhost:3000). You will be asked to sign in.

A prepared account is seeded on startup:

| Field | Value |
| --- | --- |
| Name | Arun Kumar |
| Email | vaahee21@gmail.com |
| Password | password |
| Designation | Statistical Officer |
| Organisation | National Statistical Office |

You can also register a new officer. The designation and organisation entered on the form are what the header and account page show.

Copy `backend/.env.example` to `backend/.env` and `frontend/.env.example` to `frontend/.env.local` if those files are not already present. Do not commit `.env` files.

## Layout

```text
STAT-Learn/
├── frontend/          Next.js learner and admin screens
├── backend/           Scoring, accounts, catalogue, MCQ review
├── ai-service/        Optional MCQ drafting
├── docs/
└── docker-compose.yml
```

## Scoring rule

A level is met only when it was attempted and at least 60% of its answers are correct. The gap is the target level minus the highest level where every lower level is also met. Status is Meets Target at gap 0, Moderate Gap at gap 1, and Priority Gap at gap 2 or more. Course completion uses the same 60% rule on that course's questions.
