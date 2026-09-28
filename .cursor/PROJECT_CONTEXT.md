# Project context

Why Not 6 is the Smart India Hackathon 2026 entry for problem **SIH26101**. The screening demo reuses the existing three-service application in `STAT-Learn/`. That application was built as **manthaino**, an adaptive career-learning product for Exasol Devjam. The product being demonstrated is:

**Why Not 6 — AI-Powered Competency & Learning Intelligence Platform for India's Official Statistical System.**

This file records what the repository is today, what the hackathon problem requires, and the rule that keeps competency scoring outside the language model. It does not change application code.

## Hackathon identity

| Item | Value |
| --- | --- |
| Team | Why Not 6 |
| Team ID | 176881 |
| Problem | SIH26101 |
| Ministry | Ministry of Statistics and Programme Implementation (MoSPI) |
| Theme | Smart Education |
| Category | Software |
| Pitch deck | `Why_Not_6.pptx` at the workspace root |

Problem title: develop an AI-enabled learning platform that identifies competency gaps, recommends personalized training through the iGOT Karmayogi ecosystem, and generates quizzes and MCQs from uploaded learning materials to strengthen capacity building in India's Official Statistical System.

The deck's audience is statistical officers and Official Statistical System staff, training admins at the National Statistical Systems Training Academy (NSSTA), and supervisors who need a role-to-training-to-proficiency loop. FRAC (Framework of Roles, Activities and Competencies) is the alignment model. iGOT courses and NSSTA Training Programme Advisory Committee (TPAC) programmes are the two official catalogues the pathway blends.

## What the repository is today

The running product name in code and UI is manthaino ("LEARN on ur phase"). README, auth copy, and onboarding describe a learner who picks any career role, receives an AI-authored path of software courses, and confirms mastery after a tutor flags a node ready. Capstone projects and a Python practice pad sit beside that loop.

| Service | Location | Port | Role today |
| --- | --- | --- | --- |
| Frontend | `STAT-Learn/frontend` | 3000 | Next.js 16 App Router, React 19, Tailwind, dark sidebar shell |
| Backend | `STAT-Learn/backend` | 8000 | FastAPI. Cookie sessions, paths, nodes, lessons, projects |
| AI service | `STAT-Learn/ai-service` | 8001 | LangGraph tutor, pathway generator, project mentor |
| Cache | Redis | 6379 | Sessions, path snapshots, lesson and assessment state |
| Data | Exasol Personal | 8563 | Accounts, learners, lesson notes when connected |

Learning state (paths, skills, courses, proficiency) lives mainly in `STAT-Learn/backend/app/repository/mock_db.py` and is restored from Redis. Exasol schema SQL describes a larger catalogue that the running app does not read. There is no competency framework, no L1–L5 scale, no document pipeline, and no admin review queue.

Frontend routes that exist:

- Wired in the sidebar: `/dashboard`, `/path`, `/workspace`, `/projects`, `/progress`, `/profile`
- Auth and entry: `/` redirects to `/onboarding`; `/auth/login`, `/auth/signup`
- Present, not in the live sidebar: `/assessment`, `/goal`, `/chat`
- Focus lesson: `/lesson/[id]` (sidebar hidden)

Domain language today is career role, skill, node, mastery, and capstone. Representative catalogue content is Data Engineer, Backend, Frontend, AI Engineer, MLOps, Python, SQL, React, and similar. Nothing in the services names STAT, TECH, GOV, BEH, iGOT, NSSTA, TPAC, or a statistical officer role.

## Target product for SIH26101

The platform profiles officials, diagnoses competency gaps, and routes them through one explainable pathway across mock iGOT and NSSTA/TPAC catalogues. Trainers upload learning material; the system drafts source-grounded MCQs; a human admin approves them before a learner can take them.

### Competency domains

| Code | Domain | Examples named by the problem |
| --- | --- | --- |
| STAT | Statistical | Survey design, sampling, national accounts, price, labour, agricultural and industrial statistics, SDG indicators, metadata, data quality |
| TECH | Technical | Python, R, SQL, statistical packages, GIS, visualization, AI/ML, cloud, APIs, open data |
| GOV | Digital governance | Cybersecurity, data privacy, digital signatures, government cloud, digital public infrastructure |
| BEH | Behavioural and managerial | Leadership, communication, project management, ethics, decision making, change management |

### Proficiency

Levels are **L1, L2, L3, L4, L5**. A level is an integer on that scale. The current app stores proficiency as a 0–1 float. The screening demo uses the five-level scale.

### Screening learner

| Field | Value |
| --- | --- |
| Name | Arun Kumar |
| Role | Statistical Officer |

His required levels come from a fixed role profile for that designation. They are seed data, not model output.

## Authority boundary

Competency score and gap arithmetic are deterministic and explainable. The language model is not the authority for them.

The model may assist with:

- MCQ generation
- document understanding
- retrieval
- explanation
- translation
- learning assistance

The model must not determine:

- competency score
- gap arithmetic
- authorization
- prerequisite validation
- final publication of MCQs

The current backend already scores a small mock quiz by answer-key comparison in `STAT-Learn/backend/app/services/assessment_scoring.py`. That function is the pattern to keep. Several other paths still let a client or the model supply a score, a pass flag, or a mastery signal. Those paths are recorded in `DECISIONS.md` and `MIGRATION_PLAN.md` and are not the scoring authority for this product.

## Catalogues

| Catalogue | Meaning in this product |
| --- | --- |
| iGOT | Mission Karmayogi course modules |
| NSSTA | Training programmes of the National Statistical Systems Training Academy |
| TPAC | NSSTA Training Programme Advisory Committee recommended programmes |

The screening demo uses synthetic catalogue adapters. Item titles, codes, and descriptions are original demo seed data shaped like public programme categories. They are not scraped course text and they are not responses from a government API. Copy in the demo labels them as synthetic.

## What this phase does

Documentation under `.cursor/` only:

- `PROJECT_CONTEXT.md` — this file
- `DEMO_SCOPE.md` — screening features
- `DEMO_FLOW.md` — the 5–7 minute demonstration
- `ARCHITECTURE.md` — current system and the demo target
- `MIGRATION_PLAN.md` — keep, refactor, replace, remove later
- `DECISIONS.md` — rules the later implementation must follow

Application code, UI, prompts, and data files stay as they are until a later phase implements the screening demo.
