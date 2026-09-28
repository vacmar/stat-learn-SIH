import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import (
    admin_mcq,
    assessments,
    auth,
    competency,
    conversations,
    goals,
    learners,
    lessons,
    nodes,
    onboarding,
    paths,
    projects,
    verification,
    workspace,
)
from app.repository import exasol_db
from app.services import demo_seed

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if exasol_db.EXASOL_ENABLED:
        exasol_db.init_db()
    else:
        logger.info("EXASOL_ENABLED=false; using local SQLite at backend/data/statlearn.sqlite")
        demo_seed.seed_local_database()
        demo_seed.seed_screening_result()
    yield


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="manthaino Backend MVP", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(goals.router)
app.include_router(learners.router)
app.include_router(competency.assessment_router)
app.include_router(competency.competency_router)
app.include_router(admin_mcq.router)
app.include_router(assessments.router)
app.include_router(paths.router)
app.include_router(nodes.router)
app.include_router(lessons.router)
app.include_router(conversations.router)
app.include_router(projects.router)
app.include_router(onboarding.router)
app.include_router(verification.router)
app.include_router(workspace.router)


@app.get("/health", tags=["Health"])
def health_check():
    exasol_ok = False
    if exasol_db.exasol_configured():
        try:
            conn = exasol_db.get_connection(max_attempts=1, quick=True)
            conn.close()
            exasol_ok = True
        except Exception:
            exasol_ok = False
    return {
        "status": "ok",
        "exasol_enabled": exasol_db.EXASOL_ENABLED,
        "exasol_connected": exasol_ok,
    }
