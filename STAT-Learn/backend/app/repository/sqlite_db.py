"""Local SQLite store for accounts and learners. Used when Exasol is off."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.models.domain import Account, Learner

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "statlearn.sqlite"


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


LEARNER_TEXT_COLUMNS = (
    "posting",
    "ministry",
    "state_name",
    "department",
    "organisation",
    "designation",
)


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                account_id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                is_active INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS learners (
                learner_id TEXT PRIMARY KEY,
                account_id TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                target_role_id TEXT,
                posting TEXT,
                ministry TEXT,
                state_name TEXT,
                department TEXT,
                organisation TEXT,
                designation TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS registration_options (
                option_id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                posting TEXT NOT NULL,
                parent_label TEXT,
                label TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS course_progress (
                learner_id TEXT NOT NULL,
                programme_id TEXT NOT NULL,
                correct_count INTEGER NOT NULL,
                question_count INTEGER NOT NULL,
                passed INTEGER NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (learner_id, programme_id)
            );
            CREATE TABLE IF NOT EXISTS igot_courses (
                course_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                provider TEXT NOT NULL,
                duration_seconds INTEGER,
                language TEXT,
                keywords TEXT NOT NULL,
                competency TEXT,
                external_url TEXT NOT NULL,
                fetched_at TEXT NOT NULL
            );
            """
        )
        existing = {row[1] for row in conn.execute("PRAGMA table_info(learners)")}
        for column in LEARNER_TEXT_COLUMNS:
            if column not in existing:
                conn.execute(f"ALTER TABLE learners ADD COLUMN {column} TEXT")


def upsert_account(account: Account) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO accounts (account_id, email, password_hash, created_at, updated_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(account_id) DO UPDATE SET
                email=excluded.email,
                password_hash=excluded.password_hash,
                updated_at=excluded.updated_at,
                is_active=excluded.is_active
            """,
            (
                account.account_id,
                account.email,
                account.password_hash,
                account.created_at,
                account.updated_at,
                1 if account.is_active else 0,
            ),
        )


def upsert_learner(learner: Learner) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO learners (
                learner_id, account_id, name, email, target_role_id,
                posting, ministry, state_name, department, organisation, designation,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(learner_id) DO UPDATE SET
                account_id=excluded.account_id,
                name=excluded.name,
                email=excluded.email,
                target_role_id=excluded.target_role_id,
                posting=excluded.posting,
                ministry=excluded.ministry,
                state_name=excluded.state_name,
                department=excluded.department,
                organisation=excluded.organisation,
                designation=excluded.designation,
                updated_at=excluded.updated_at
            """,
            (
                learner.learner_id,
                learner.account_id,
                learner.name,
                learner.email,
                learner.target_role_id,
                learner.posting,
                learner.ministry,
                learner.state_name,
                learner.department,
                learner.organisation,
                learner.designation,
                learner.created_at,
                learner.updated_at,
            ),
        )


def load_into(db: dict) -> None:
    init_db()
    accounts = db.setdefault("accounts", {})
    by_id = db.setdefault("learners_by_id", {})
    by_account = db.setdefault("learners_by_account", {})
    with connect() as conn:
        for row in conn.execute("SELECT * FROM accounts"):
            accounts[row["account_id"]] = Account(
                account_id=row["account_id"],
                email=row["email"],
                password_hash=row["password_hash"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                is_active=bool(row["is_active"]),
            )
        for row in conn.execute("SELECT * FROM learners"):
            learner = Learner(
                learner_id=row["learner_id"],
                account_id=row["account_id"],
                name=row["name"],
                email=row["email"],
                target_role_id=row["target_role_id"],
                posting=row["posting"],
                ministry=row["ministry"],
                state_name=row["state_name"],
                department=row["department"],
                organisation=row["organisation"],
                designation=row["designation"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            by_id[learner.learner_id] = learner
            by_account[learner.account_id] = learner


def replace_registration_options(rows: list[tuple[str, str, str, str | None, str]]) -> None:
    init_db()
    with connect() as conn:
        conn.executemany(
            """
            INSERT INTO registration_options (option_id, kind, posting, parent_label, label)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(option_id) DO UPDATE SET
                kind=excluded.kind,
                posting=excluded.posting,
                parent_label=excluded.parent_label,
                label=excluded.label
            """,
            rows,
        )


def registration_options() -> list[dict]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            "SELECT kind, posting, parent_label, label FROM registration_options ORDER BY kind, label"
        ).fetchall()
    return [dict(row) for row in rows]


def prepared_registration() -> dict | None:
    init_db()
    with connect() as conn:
        row = conn.execute(
            """
            SELECT name, email, posting, ministry, state_name, department, organisation, designation
            FROM learners
            WHERE designation IS NOT NULL AND trim(designation) != ''
            ORDER BY created_at
            LIMIT 1
            """
        ).fetchone()
    if row is None:
        return None
    return dict(row)


def _progress_row(row: sqlite3.Row) -> dict:
    total = int(row["question_count"])
    correct = int(row["correct_count"])
    return {
        "programme_id": row["programme_id"],
        "correct_count": correct,
        "question_count": total,
        "passed": bool(row["passed"]),
        "status": "Completed" if row["passed"] else "Not yet",
        "updated_at": row["updated_at"],
    }


def get_course_progress(learner_id: str, programme_id: str) -> dict | None:
    init_db()
    with connect() as conn:
        row = conn.execute(
            """
            SELECT programme_id, correct_count, question_count, passed, updated_at
            FROM course_progress
            WHERE learner_id = ? AND programme_id = ?
            """,
            (learner_id, programme_id),
        ).fetchone()
    if row is None:
        return None
    return _progress_row(row)


def list_course_progress(learner_id: str) -> list[dict]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT programme_id, correct_count, question_count, passed, updated_at
            FROM course_progress
            WHERE learner_id = ?
            ORDER BY programme_id
            """,
            (learner_id,),
        ).fetchall()
    return [_progress_row(row) for row in rows]


def save_course_progress(learner_id: str, programme_id: str, correct: int, total: int, passed: bool, updated_at: str) -> dict:
    init_db()
    with connect() as conn:
        previous = conn.execute(
            "SELECT passed FROM course_progress WHERE learner_id = ? AND programme_id = ?",
            (learner_id, programme_id),
        ).fetchone()
        keep_passed = bool(passed or (previous and previous["passed"]))
        conn.execute(
            """
            INSERT INTO course_progress (learner_id, programme_id, correct_count, question_count, passed, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(learner_id, programme_id) DO UPDATE SET
                correct_count=excluded.correct_count,
                question_count=excluded.question_count,
                passed=excluded.passed,
                updated_at=excluded.updated_at
            """,
            (learner_id, programme_id, correct, total, 1 if keep_passed else 0, updated_at),
        )
    stored = get_course_progress(learner_id, programme_id)
    assert stored is not None
    return stored


def replace_igot_courses(rows: list[dict], fetched_at: str) -> None:
    init_db()
    with connect() as conn:
        conn.execute("DELETE FROM igot_courses")
        conn.executemany(
            """
            INSERT INTO igot_courses (
                course_id, name, provider, duration_seconds, language, keywords, competency, external_url, fetched_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row["course_id"],
                    row["name"],
                    row["provider"],
                    row.get("duration_seconds"),
                    row.get("language"),
                    row["keywords"],
                    row.get("competency"),
                    row["external_url"],
                    fetched_at,
                )
                for row in rows
            ],
        )


def list_igot_courses() -> list[dict]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT course_id, name, provider, duration_seconds, language, keywords, competency, external_url, fetched_at
            FROM igot_courses
            ORDER BY name
            """
        ).fetchall()
    found = []
    for row in rows:
        item = dict(row)
        item["keywords"] = json.loads(item["keywords"] or "[]")
        found.append(item)
    return found
