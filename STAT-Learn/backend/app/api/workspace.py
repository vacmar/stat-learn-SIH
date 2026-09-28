"""Lightweight practice-pad execution (local/demo). Not a hardened sandbox."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/workspace", tags=["Workspace"])

MAX_CODE_CHARS = 20_000
TIMEOUT_SEC = 4
MAX_OUTPUT_CHARS = 8_000


class ExecuteRequest(BaseModel):
    code: str = Field(..., min_length=1)
    language: str = "python"


class ExecuteResponse(BaseModel):
    ok: bool
    stdout: str
    stderr: str
    exit_code: int | None
    timed_out: bool
    language: str


@router.post("/execute", response_model=ExecuteResponse)
def execute_code(body: ExecuteRequest) -> ExecuteResponse:
    language = (body.language or "python").strip().lower()
    if language not in {"python", "py"}:
        raise HTTPException(
            status_code=400,
            detail="Only Python is supported in the practice workspace right now.",
        )

    code = body.code
    if len(code) > MAX_CODE_CHARS:
        raise HTTPException(
            status_code=400,
            detail=f"Code exceeds {MAX_CODE_CHARS} character limit.",
        )

    with tempfile.TemporaryDirectory(prefix="manthaino-ws-") as tmp:
        script = Path(tmp) / "main.py"
        script.write_text(code, encoding="utf-8")
        try:
            proc = subprocess.run(
                [sys.executable, str(script)],
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SEC,
                cwd=tmp,
                check=False,
                env={
                    "PATH": "/usr/local/bin:/usr/bin:/bin",
                    "PYTHONUNBUFFERED": "1",
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "HOME": tmp,
                },
            )
        except subprocess.TimeoutExpired as exc:
            stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
            stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
            return ExecuteResponse(
                ok=False,
                stdout=_clip(stdout),
                stderr=_clip(stderr or f"Timed out after {TIMEOUT_SEC}s"),
                exit_code=None,
                timed_out=True,
                language="python",
            )

    return ExecuteResponse(
        ok=proc.returncode == 0,
        stdout=_clip(proc.stdout or ""),
        stderr=_clip(proc.stderr or ""),
        exit_code=proc.returncode,
        timed_out=False,
        language="python",
    )


def _clip(text: str) -> str:
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return text[: MAX_OUTPUT_CHARS - 20] + "\n… (truncated)"
