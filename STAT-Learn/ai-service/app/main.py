from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, path, tools
from app.core.config import settings
from app.tools.registry import ALL_TOOLS

app = FastAPI(
    title=settings.app_name,
    description="Adaptive AI Tutor, Pathway Reasoner, and Project Mentor Orchestrator for manthaino",
    version="0.1.0",
)

# Enable CORS for Next.js frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(path.router)
app.include_router(tools.router)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "provider": settings.llm_provider,
        "tools_registered": len(ALL_TOOLS),
    }
