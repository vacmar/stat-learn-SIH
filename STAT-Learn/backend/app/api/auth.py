import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

from app.core.cache import drop_session, load_session, save_session
from app.models.domain import Account, Learner
from app.repository import sqlite_db, state_repo

router = APIRouter(prefix="/auth", tags=["Auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SESSION_COOKIE_NAME = "session_id"
SESSION_EXPIRY = 86400 * 7  # 7 days


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def normalize_email(email: str) -> str:
    return email.strip().lower()


class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    posting: str | None = None
    ministry: str | None = None
    state_name: str | None = None
    department: str | None = None
    organisation: str | None = None
    designation: str | None = None


def _clean(value: str | None) -> str | None:
    text = (value or "").strip()
    return text or None


def registration_fields(req: SignupRequest) -> dict:
    posting = (_clean(req.posting) or "").lower()
    if posting not in {"", "center", "state"}:
        raise HTTPException(status_code=422, detail="Choose Center or State.")
    if posting == "center":
        ministry = _clean(req.ministry)
        organisation = _clean(req.organisation)
        designation = _clean(req.designation)
        if not ministry or not organisation or not designation:
            raise HTTPException(
                status_code=422,
                detail="Choose a ministry, organisation, and designation.",
            )
        return {
            "posting": "center",
            "ministry": ministry,
            "state_name": None,
            "department": None,
            "organisation": organisation,
            "designation": designation,
            "target_role_id": designation.lower().replace(" ", "_"),
        }
    if posting == "state":
        state_name = _clean(req.state_name)
        department = _clean(req.department)
        organisation = _clean(req.organisation)
        designation = _clean(req.designation)
        if not state_name or not department or not organisation or not designation:
            raise HTTPException(
                status_code=422,
                detail="Choose a state, department, organisation, and designation.",
            )
        return {
            "posting": "state",
            "ministry": None,
            "state_name": state_name,
            "department": department,
            "organisation": organisation,
            "designation": designation,
            "target_role_id": designation.lower().replace(" ", "_"),
        }
    return {
        "posting": None,
        "ministry": None,
        "state_name": None,
        "department": None,
        "organisation": None,
        "designation": None,
        "target_role_id": None,
    }


def public_registration(learner: Learner) -> dict:
    return {
        "name": learner.name,
        "email": learner.email,
        "posting": learner.posting,
        "ministry": learner.ministry,
        "state_name": learner.state_name,
        "department": learner.department,
        "organisation": learner.organisation,
        "designation": learner.designation,
    }


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def get_current_account_id(request: Request) -> str:
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    cache = load_session(session_id)
    if not cache:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    return cache


def get_current_account(account_id: str = Depends(get_current_account_id)) -> Account:
    account = state_repo.get_account_by_id(account_id)
    if not account:
        raise HTTPException(status_code=401, detail="Account not found")
    return account


def get_current_learner(account_id: str = Depends(get_current_account_id)) -> Learner:
    learner = state_repo.get_learner_by_account(account_id)
    if not learner:
        raise HTTPException(
            status_code=404, detail="Learner profile not found for account"
        )
    return learner


@router.get("/registration-form")
def registration_form():
    return {
        "profile": sqlite_db.prepared_registration(),
        "options": sqlite_db.registration_options(),
    }


@router.post("/signup")
def signup(req: SignupRequest, response: Response):
    email = normalize_email(req.email)
    fields = registration_fields(req)

    if len(req.password) < 6:
        raise HTTPException(status_code=422, detail="Password too short")

    existing = state_repo.get_account_by_email(email)
    if existing:
        # Repair orphan accounts created when learner insert previously failed
        if not verify_password(req.password, existing.password_hash):
            raise HTTPException(status_code=409, detail="Email already registered")
        learner = state_repo.get_learner_by_account(existing.account_id)
        if learner:
            raise HTTPException(status_code=409, detail="Email already registered")
        now = datetime.now(UTC).isoformat()
        learner = Learner(
            learner_id=f"lrn_{uuid.uuid4().hex}",
            account_id=existing.account_id,
            name=req.name,
            email=email,
            created_at=now,
            updated_at=now,
            **fields,
        )
        state_repo.create_learner(learner)
        session_id = uuid.uuid4().hex
        save_session(session_id, existing.account_id, SESSION_EXPIRY)
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_id,
            httponly=True,
            max_age=SESSION_EXPIRY,
            path="/",
            samesite="lax",
            secure=False,
        )
        return {
            "message": "Signup repaired — learner profile created",
            "account_id": existing.account_id,
            "learner_id": learner.learner_id,
            "name": learner.name,
        }

    now = datetime.now(UTC).isoformat()
    account_id = f"acc_{uuid.uuid4().hex}"

    account = Account(
        account_id=account_id,
        email=email,
        password_hash=get_password_hash(req.password),
        created_at=now,
        updated_at=now,
        is_active=True,
    )

    learner_id = f"lrn_{uuid.uuid4().hex}"
    learner = Learner(
        learner_id=learner_id,
        account_id=account_id,
        name=req.name,
        email=email,
        created_at=now,
        updated_at=now,
        **fields,
    )

    state_repo.create_account(account)
    state_repo.create_learner(learner)

    session_id = uuid.uuid4().hex
    save_session(session_id, account_id, SESSION_EXPIRY)

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        max_age=SESSION_EXPIRY,
        path="/",
        samesite="lax",
        secure=False,
    )

    return {
        "message": "Signup successful",
        "account_id": account_id,
        "learner_id": learner_id,
        "name": learner.name,
    }


@router.post("/login")
def login(req: LoginRequest, response: Response):
    email = normalize_email(req.email)
    account = state_repo.get_account_by_email(email)

    # Auto-provisioning for testing without signup
    if not account and req.password == "password":
        account_id = f"acc_{uuid.uuid4().hex[:8]}"
        learner_id = f"lrn_{uuid.uuid4().hex[:8]}"
        now = datetime.now(UTC).isoformat()

        account = Account(
            account_id=account_id,
            email=email,
            password_hash=get_password_hash(req.password),
            created_at=now,
            updated_at=now,
            is_active=True,
        )
        state_repo.create_account(account)

        learner = Learner(
            learner_id=learner_id,
            account_id=account_id,
            name=email.split("@")[0],
            email=email,
            created_at=now,
            updated_at=now,
        )
        state_repo.create_learner(learner)

    if not account or not verify_password(req.password, account.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    learner = state_repo.get_learner_by_account(account.account_id)
    if not learner:
        # Repair orphan account (account row without learner)
        now = datetime.now(UTC).isoformat()
        learner = Learner(
            learner_id=f"lrn_{uuid.uuid4().hex}",
            account_id=account.account_id,
            name=email.split("@")[0],
            email=email,
            created_at=now,
            updated_at=now,
        )
        state_repo.create_learner(learner)

    session_id = uuid.uuid4().hex
    save_session(session_id, account.account_id, SESSION_EXPIRY)

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        max_age=SESSION_EXPIRY,
        path="/",
        samesite="lax",
        secure=False,
    )

    return {
        "message": "Login successful",
        "account_id": account.account_id,
        "learner_id": learner.learner_id,
        "onboarding_completed": learner.onboarding_completed,
    }


@router.post("/logout")
def logout(request: Request, response: Response):
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id:
        drop_session(session_id)

    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return {"message": "Logged out successfully"}


@router.get("/me")
def get_me(
    account: Account = Depends(get_current_account),
    learner: Learner = Depends(get_current_learner),
):
    return {
        "account_id": account.account_id,
        "email": account.email,
        "learner_id": learner.learner_id,
        "name": learner.name,
        "onboarding_completed": learner.onboarding_completed,
        **public_registration(learner),
    }
