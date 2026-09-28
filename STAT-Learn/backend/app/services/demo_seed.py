"""Seed the local SQLite database and the screening competency result."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from passlib.context import CryptContext

from app.data.diagnostic_seed import DEMO_LEARNER_ID, QUESTIONS, SCREENING_ANSWER_INDEX
from app.models.domain import Account, Learner
from app.repository import sqlite_db, state_repo
from app.services import competency_store

logger = logging.getLogger(__name__)

DEMO_EMAIL = "vaahee21@gmail.com"
DEMO_PASSWORD = "password"
DEMO_ACCOUNT_ID = "account_arun_kumar"
PREPARED_POSTING = "center"
PREPARED_MINISTRY = "Ministry of Statistics and Programme Implementation"
PREPARED_ORGANISATION = "National Statistical Office"
PREPARED_DESIGNATION = "Statistical Officer"
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

_MOSPI = PREPARED_MINISTRY
_OPTIONS = [
    ("ministry:mospi", "ministry", "center", None, _MOSPI),
    ("ministry:education", "ministry", "center", None, "Ministry of Education"),
    ("ministry:finance", "ministry", "center", None, "Ministry of Finance"),
    ("organisation:nso", "organisation", "center", _MOSPI, PREPARED_ORGANISATION),
    ("organisation:nssta", "organisation", "center", _MOSPI, "National Statistical Systems Training Academy"),
    ("organisation:ncert", "organisation", "center", "Ministry of Education", "National Council of Educational Research and Training"),
    ("state:tn", "state", "state", None, "Tamil Nadu"),
    ("state:ka", "state", "state", None, "Karnataka"),
    ("state:mh", "state", "state", None, "Maharashtra"),
    ("department:tn-des", "department", "state", "Tamil Nadu", "Directorate of Economics and Statistics"),
    ("department:ka-des", "department", "state", "Karnataka", "Directorate of Economics and Statistics"),
    ("department:mh-des", "department", "state", "Maharashtra", "Directorate of Economics and Statistics"),
    ("organisation:tn-des", "organisation", "state", "Tamil Nadu", "Directorate of Economics and Statistics, Tamil Nadu"),
    ("organisation:ka-des", "organisation", "state", "Karnataka", "Directorate of Economics and Statistics, Karnataka"),
    ("organisation:mh-des", "organisation", "state", "Maharashtra", "Directorate of Economics and Statistics, Maharashtra"),
    ("designation:so", "designation", "both", None, PREPARED_DESIGNATION),
    ("designation:jso", "designation", "both", None, "Junior Statistical Officer"),
    ("designation:dd", "designation", "both", None, "Deputy Director"),
    ("designation:dir", "designation", "both", None, "Director"),
]


def _fill_prepared_registration(learner: Learner) -> None:
    if (learner.designation or "").strip():
        return
    learner.posting = PREPARED_POSTING
    learner.ministry = PREPARED_MINISTRY
    learner.state_name = None
    learner.department = None
    learner.organisation = PREPARED_ORGANISATION
    learner.designation = PREPARED_DESIGNATION
    learner.target_role_id = learner.target_role_id or "statistical_officer"
    state_repo.update_learner(learner)


def seed_local_database() -> None:
    sqlite_db.replace_registration_options(_OPTIONS)
    sqlite_db.load_into(state_repo.db)
    existing_learner = next(
        (
            item
            for item in state_repo.db.get("learners_by_id", {}).values()
            if getattr(item, "email", None) == DEMO_EMAIL or item.learner_id == DEMO_LEARNER_ID
        ),
        None,
    )
    if state_repo.get_account_by_email(DEMO_EMAIL) and existing_learner and existing_learner.learner_id == DEMO_LEARNER_ID:
        _fill_prepared_registration(existing_learner)
        return
    now = datetime.now(UTC).isoformat()
    account = Account(
        account_id=DEMO_ACCOUNT_ID,
        email=DEMO_EMAIL,
        password_hash=_pwd.hash(DEMO_PASSWORD),
        created_at=now,
        updated_at=now,
    )
    learner = Learner(
        learner_id=DEMO_LEARNER_ID,
        account_id=DEMO_ACCOUNT_ID,
        name="Arun Kumar",
        email=DEMO_EMAIL,
        target_role_id="statistical_officer",
        posting=PREPARED_POSTING,
        ministry=PREPARED_MINISTRY,
        organisation=PREPARED_ORGANISATION,
        designation=PREPARED_DESIGNATION,
        created_at=now,
        updated_at=now,
        onboarding_completed=True,
    )
    state_repo.create_account(account)
    state_repo.create_learner(learner)
    logger.info("Seeded local account %s as Arun Kumar", DEMO_EMAIL)


def seed_screening_result() -> None:
    if competency_store.latest_completed(DEMO_LEARNER_ID):
        return
    attempt = competency_store.create_attempt(DEMO_LEARNER_ID)
    for question in QUESTIONS:
        index = SCREENING_ANSWER_INDEX.get(question.id, 0)
        current = competency_store.get_attempt(attempt["attempt_id"])
        if current is None:
            return
        competency_store.record_answer(current, question.id, question.options[index])
    finished = competency_store.get_attempt(attempt["attempt_id"])
    if finished:
        competency_store.complete_attempt(finished)
        logger.info("Seeded screening diagnostic for %s", DEMO_LEARNER_ID)
