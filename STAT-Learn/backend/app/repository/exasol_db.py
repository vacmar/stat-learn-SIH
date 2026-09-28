import logging
import os
import ssl
from pathlib import Path

import pyexasol
from dotenv import load_dotenv

load_dotenv()

from app.models.domain import Account, Learner

logger = logging.getLogger(__name__)

EXASOL_DSN = os.getenv("EXASOL_DSN", "127.0.0.1:8563")
EXASOL_USER = os.getenv("EXASOL_USER", "sys")
EXASOL_PASSWORD = os.getenv("EXASOL_PASSWORD", "")
EXASOL_PASSWORD_FILE = os.getenv("EXASOL_PASSWORD_FILE", "")


def _env_bool(name: str, default: bool = True) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


EXASOL_ENABLED = _env_bool("EXASOL_ENABLED", False)


def _read_password_from_file(path: str) -> str:
    try:
        return Path(path).expanduser().read_text(encoding="utf-8").strip()
    except OSError as e:
        logger.warning("Could not read EXASOL_PASSWORD_FILE: %s", e)
        return ""


def resolve_password() -> str:
    if EXASOL_PASSWORD:
        return EXASOL_PASSWORD
    if EXASOL_PASSWORD_FILE:
        return _read_password_from_file(EXASOL_PASSWORD_FILE)
    return ""


def exasol_configured() -> bool:
    if not EXASOL_ENABLED:
        return False
    if not EXASOL_DSN or not EXASOL_USER:
        return False
    return bool(resolve_password())


def get_connection(*, max_attempts: int | None = None, quick: bool = False):
    if not exasol_configured():
        raise RuntimeError("Exasol is disabled or not configured")

    import time

    password = resolve_password()
    if quick:
        attempts = max_attempts if max_attempts is not None else 1
        delay = 0.0
    elif max_attempts is not None:
        attempts = max_attempts
        delay = 0.5
    else:
        attempts = 5
        delay = 1.0

    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            return pyexasol.connect(
                dsn=EXASOL_DSN,
                user=EXASOL_USER,
                password=password,
                schema="MANTHAINO",
                compression=True,
                websocket_sslopt={"cert_reqs": ssl.CERT_NONE},
            )
        except Exception as e:
            last_error = e
            if attempt >= attempts - 1:
                raise
            if delay:
                time.sleep(delay)
    if last_error:
        raise last_error
    raise RuntimeError("Failed to connect to Exasol")


def init_db() -> bool:
    """Initialize Exasol schema/tables. Returns True on success, False if skipped or failed."""
    if not exasol_configured():
        logger.info("Skipping Exasol init (disabled or missing credentials)")
        return False
    try:
        conn = get_connection(max_attempts=3, quick=False)
        try:
            conn.execute("CREATE SCHEMA IF NOT EXISTS MANTHAINO")
            conn.execute("OPEN SCHEMA MANTHAINO")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    account_id VARCHAR(50) PRIMARY KEY,
                    email VARCHAR(255),
                    password_hash VARCHAR(255),
                    created_at VARCHAR(50),
                    updated_at VARCHAR(50),
                    is_active BOOLEAN
                )
            """)
            # Exasol does not support UNIQUE column constraints; enforce uniqueness in app code.

            conn.execute("""
                CREATE TABLE IF NOT EXISTS learners (
                    learner_id VARCHAR(50) PRIMARY KEY,
                    account_id VARCHAR(50) REFERENCES accounts(account_id),
                    name VARCHAR(255),
                    target_role_id VARCHAR(50),
                    target_domain VARCHAR(100),
                    experience_level VARCHAR(50),
                    prior_experience VARCHAR(50),
                    education VARCHAR(100),
                    learning_style VARCHAR(50),
                    weekly_time INT,
                    onboarding_completed BOOLEAN,
                    onboarding_version INT,
                    onboarding_completed_at VARCHAR(50),
                    created_at VARCHAR(50),
                    updated_at VARCHAR(50),
                    goals VARCHAR(2000),
                    known_skills VARCHAR(2000),
                    interests VARCHAR(2000),
                    self_reported_proficiency VARCHAR(4000)
                )
            """)

            # Lesson workspace: rich notes + chat transcript (no FK to path_nodes —
            # AI-generated node IDs may not live in Exasol path_nodes yet).
            conn.execute("""
                CREATE TABLE IF NOT EXISTS lesson_sessions (
                    session_key VARCHAR(200) PRIMARY KEY,
                    learner_id VARCHAR(50),
                    node_id VARCHAR(100),
                    practice_notes VARCHAR(2000000),
                    messages_json VARCHAR(2000000),
                    ai_ready BOOLEAN,
                    ready_reason VARCHAR(1000),
                    updated_at VARCHAR(50)
                )
            """)
        finally:
            conn.close()
        logger.info("Exasol schema initialized")
        return True
    except Exception as e:
        logger.warning("Failed to initialize Exasol DB (continuing without): %s", e)
        return False


# ==========================================
# Account Repository Operations
# ==========================================


def create_account(account: Account):
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO accounts (account_id, email, password_hash, created_at, updated_at, is_active)
            VALUES ({account_id}, {email}, {password_hash}, {created_at}, {updated_at}, {is_active})
            """,
            {
                "account_id": account.account_id,
                "email": account.email,
                "password_hash": account.password_hash,
                "created_at": account.created_at,
                "updated_at": account.updated_at,
                "is_active": account.is_active,
            },
        )
    finally:
        conn.close()


def get_account_by_email(email: str) -> Account | None:
    conn = get_connection()
    try:
        stmt = conn.execute(
            "SELECT * FROM accounts WHERE email = {email}", {"email": email}
        )
        row = stmt.fetchone()
        if row:
            return Account(
                account_id=row[0],
                email=row[1],
                password_hash=row[2],
                created_at=row[3],
                updated_at=row[4],
                is_active=row[5],
            )
        return None
    finally:
        conn.close()


def get_account_by_id(account_id: str) -> Account | None:
    conn = get_connection()
    try:
        stmt = conn.execute(
            "SELECT * FROM accounts WHERE account_id = {account_id}",
            {"account_id": account_id},
        )
        row = stmt.fetchone()
        if row:
            return Account(
                account_id=row[0],
                email=row[1],
                password_hash=row[2],
                created_at=row[3],
                updated_at=row[4],
                is_active=row[5],
            )
        return None
    finally:
        conn.close()


# ==========================================
# Learner Repository Operations
# ==========================================

import json


def _exa_ts(value: str | None) -> str | None:
    """Convert ISO timestamps to Exasol TIMESTAMP literal format."""
    if not value:
        return None
    # 2026-09-13T09:52:10.355005+00:00 -> 2026-09-13 09:52:10.355005
    cleaned = value.replace("T", " ")
    for sep in ("+", "Z"):
        if sep in cleaned[10:]:
            cleaned = cleaned[: cleaned.index(sep, 10)]
            break
    return cleaned.strip()


def _row_to_learner(row: tuple) -> Learner:
    """Map SELECT column order used by get_learner* queries."""
    return Learner(
        learner_id=row[0],
        account_id=row[1],
        name=row[2],
        email=row[3],
        target_role_id=row[4],
        target_domain=row[5],
        experience_level=row[6],
        prior_experience=row[7],
        education=row[8],
        learning_style=row[9],
        weekly_time=int(row[10]) if row[10] is not None else None,
        onboarding_completed=bool(row[11]) if row[11] is not None else False,
        onboarding_version=int(row[12]) if row[12] is not None else 1,
        onboarding_completed_at=row[13],
        created_at=str(row[14]) if row[14] is not None else "",
        updated_at=str(row[15]) if row[15] is not None else "",
        goals=json.loads(row[16]) if row[16] else [],
        known_skills=json.loads(row[17]) if row[17] else [],
        interests=json.loads(row[18]) if row[18] else [],
        self_reported_proficiency=json.loads(row[19]) if row[19] else {},
    )


_LEARNER_SELECT = """
    SELECT
        learner_id, account_id, name, email,
        target_role_id, target_domain, experience_level, prior_experience, education,
        learning_style, weekly_time, onboarding_completed, onboarding_version,
        onboarding_completed_at, created_at, updated_at,
        goals, known_skills, interests, self_reported_proficiency
    FROM learners
"""


def create_learner(learner: Learner):
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO learners (
                learner_id, account_id, name, email, target_role_id, target_domain,
                experience_level, prior_experience, education, learning_style, weekly_time,
                onboarding_completed, onboarding_version, onboarding_completed_at, created_at, updated_at,
                goals, known_skills, interests, self_reported_proficiency
            ) VALUES (
                {learner_id}, {account_id}, {name}, {email}, {target_role_id}, {target_domain},
                {experience_level}, {prior_experience}, {education}, {learning_style}, {weekly_time},
                {onboarding_completed}, {onboarding_version}, {onboarding_completed_at}, {created_at}, {updated_at},
                {goals}, {known_skills}, {interests}, {self_reported_proficiency}
            )
            """,
            {
                "learner_id": learner.learner_id,
                "account_id": learner.account_id,
                "name": learner.name,
                "email": learner.email or "",
                "target_role_id": learner.target_role_id,
                "target_domain": learner.target_domain,
                "experience_level": learner.experience_level,
                "prior_experience": learner.prior_experience,
                "education": learner.education,
                "learning_style": learner.learning_style,
                "weekly_time": learner.weekly_time,
                "onboarding_completed": learner.onboarding_completed,
                "onboarding_version": learner.onboarding_version,
                "onboarding_completed_at": learner.onboarding_completed_at,
                "created_at": _exa_ts(learner.created_at),
                "updated_at": _exa_ts(learner.updated_at),
                "goals": json.dumps(learner.goals),
                "known_skills": json.dumps(learner.known_skills),
                "interests": json.dumps(learner.interests),
                "self_reported_proficiency": json.dumps(
                    learner.self_reported_proficiency
                ),
            },
        )
    finally:
        conn.close()


def get_learner(learner_id: str) -> Learner | None:
    conn = get_connection()
    try:
        stmt = conn.execute(
            _LEARNER_SELECT + " WHERE learner_id = {learner_id}",
            {"learner_id": learner_id},
        )
        row = stmt.fetchone()
        if row:
            return _row_to_learner(row)
        return None
    finally:
        conn.close()


def get_learner_by_account(account_id: str) -> Learner | None:
    conn = get_connection()
    try:
        stmt = conn.execute(
            _LEARNER_SELECT + " WHERE account_id = {account_id}",
            {"account_id": account_id},
        )
        row = stmt.fetchone()
        if row:
            return _row_to_learner(row)
        return None
    finally:
        conn.close()


def update_learner(learner: Learner):
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE learners SET
                name = {name},
                target_role_id = {target_role_id},
                target_domain = {target_domain},
                experience_level = {experience_level},
                prior_experience = {prior_experience},
                education = {education},
                learning_style = {learning_style},
                weekly_time = {weekly_time},
                onboarding_completed = {onboarding_completed},
                onboarding_version = {onboarding_version},
                onboarding_completed_at = {onboarding_completed_at},
                updated_at = {updated_at},
                goals = {goals},
                known_skills = {known_skills},
                interests = {interests},
                self_reported_proficiency = {self_reported_proficiency}
            WHERE learner_id = {learner_id}
            """,
            {
                "learner_id": learner.learner_id,
                "name": learner.name,
                "target_role_id": learner.target_role_id,
                "target_domain": learner.target_domain,
                "experience_level": learner.experience_level,
                "prior_experience": learner.prior_experience,
                "education": learner.education,
                "learning_style": learner.learning_style,
                "weekly_time": learner.weekly_time,
                "onboarding_completed": learner.onboarding_completed,
                "onboarding_version": learner.onboarding_version,
                "onboarding_completed_at": learner.onboarding_completed_at,
                "updated_at": _exa_ts(learner.updated_at),
                "goals": json.dumps(learner.goals),
                "known_skills": json.dumps(learner.known_skills),
                "interests": json.dumps(learner.interests),
                "self_reported_proficiency": json.dumps(
                    learner.self_reported_proficiency
                ),
            },
        )
    finally:
        conn.close()


# ==========================================
# Lesson sessions (notes + chat)
# ==========================================


def upsert_lesson_session(
    *,
    session_key: str,
    learner_id: str,
    node_id: str,
    practice_notes: str | None = None,
    messages: list | None = None,
    ai_ready: bool | None = None,
    ready_reason: str | None = None,
    updated_at: str | None = None,
) -> None:
    """Insert or merge a lesson session row. None fields keep existing values."""
    if not exasol_configured():
        return
    conn = get_connection(max_attempts=2, quick=True)
    try:
        existing = conn.execute(
            """
            SELECT practice_notes, messages_json, ai_ready, ready_reason
            FROM lesson_sessions WHERE session_key = {session_key}
            """,
            {"session_key": session_key},
        ).fetchone()

        notes = practice_notes
        msgs_json = json.dumps(messages) if messages is not None else None
        ready = ai_ready
        reason = ready_reason

        if existing:
            if notes is None:
                notes = existing[0] or ""
            if msgs_json is None:
                msgs_json = existing[1] or "[]"
            if ready is None:
                ready = bool(existing[2]) if existing[2] is not None else False
            if reason is None:
                reason = existing[3]
            conn.execute(
                """
                UPDATE lesson_sessions SET
                    practice_notes = {practice_notes},
                    messages_json = {messages_json},
                    ai_ready = {ai_ready},
                    ready_reason = {ready_reason},
                    updated_at = {updated_at}
                WHERE session_key = {session_key}
                """,
                {
                    "session_key": session_key,
                    "practice_notes": notes or "",
                    "messages_json": msgs_json or "[]",
                    "ai_ready": bool(ready),
                    "ready_reason": reason,
                    "updated_at": updated_at or "",
                },
            )
        else:
            conn.execute(
                """
                INSERT INTO lesson_sessions (
                    session_key, learner_id, node_id, practice_notes, messages_json,
                    ai_ready, ready_reason, updated_at
                ) VALUES (
                    {session_key}, {learner_id}, {node_id}, {practice_notes}, {messages_json},
                    {ai_ready}, {ready_reason}, {updated_at}
                )
                """,
                {
                    "session_key": session_key,
                    "learner_id": learner_id,
                    "node_id": node_id,
                    "practice_notes": notes or "",
                    "messages_json": msgs_json or "[]",
                    "ai_ready": bool(ready) if ready is not None else False,
                    "ready_reason": reason,
                    "updated_at": updated_at or "",
                },
            )
    finally:
        conn.close()


def get_lesson_session(session_key: str) -> dict | None:
    if not exasol_configured():
        return None
    conn = get_connection(max_attempts=1, quick=True)
    try:
        row = conn.execute(
            """
            SELECT learner_id, node_id, practice_notes, messages_json,
                   ai_ready, ready_reason, updated_at
            FROM lesson_sessions WHERE session_key = {session_key}
            """,
            {"session_key": session_key},
        ).fetchone()
        if not row:
            return None
        try:
            messages = json.loads(row[3] or "[]")
        except (json.JSONDecodeError, TypeError):
            messages = []
        return {
            "learner_id": row[0],
            "node_id": row[1],
            "practice_notes": row[2] or "",
            "messages": messages if isinstance(messages, list) else [],
            "ai_ready": bool(row[4]) if row[4] is not None else False,
            "ready_reason": row[5],
            "updated_at": row[6],
        }
    finally:
        conn.close()
