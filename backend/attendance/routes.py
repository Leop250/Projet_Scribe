import os
import secrets
from collections import defaultdict
from time import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from Auth.dependencies import get_current_user
from Auth.users import UserModel
from database import get_db

from .models import RecordingSession, Signature
from .schemas import (
    PublicSessionResponse,
    SessionCreateRequest,
    SessionCreateResponse,
    SessionStatusResponse,
    SignRequest,
)

_PURGE_THRESHOLD = 1000


class _RateLimiter:
    def __init__(self, window_seconds: int, max_attempts: int):
        self.window_seconds = window_seconds
        self.max_attempts = max_attempts
        self._attempts: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, detail: str) -> None:
        now = time()
        attempts = self._attempts[key]
        attempts[:] = [t for t in attempts if now - t < self.window_seconds]
        if len(attempts) >= self.max_attempts:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail)
        attempts.append(now)

        if len(self._attempts) > _PURGE_THRESHOLD:
            self._purge_expired(now)

    def _purge_expired(self, now: float) -> None:
        expired = [k for k, v in self._attempts.items() if not v or now - v[-1] >= self.window_seconds]
        for k in expired:
            del self._attempts[k]


_session_create_rate_limiter = _RateLimiter(window_seconds=3600, max_attempts=30)
_public_status_rate_limiter = _RateLimiter(window_seconds=60, max_attempts=60)
_sign_ip_rate_limiter = _RateLimiter(window_seconds=300, max_attempts=20)
_sign_session_rate_limiter = _RateLimiter(window_seconds=3600, max_attempts=1000)


def _normalize_url(url: str) -> str:
    if not url:
        return url
    return url if url.startswith(("http://", "https://")) else f"https://{url}"


FRONTEND_URL = _normalize_url(os.environ.get("FRONTEND_URL", "http://localhost:5173"))


def _build_sign_url(token: str) -> str:
    return f"{FRONTEND_URL}/sign/{token}"


def _get_owned_session(db: Session, token: str, current_user: UserModel) -> RecordingSession:
    session = db.query(RecordingSession).filter(RecordingSession.token == token).first()
    if session is None or session.organizer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session introuvable.")
    return session


def _count_confirmed(db: Session, session_id: int) -> int:
    return db.query(Signature).filter(Signature.session_id == session_id).count()


router = APIRouter(prefix="/attendance")


@router.post("/sessions", response_model=SessionCreateResponse)
def create_session(
    body: SessionCreateRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _session_create_rate_limiter.check(str(current_user.id), "Trop de sessions créées, réessaie plus tard.")

    token = secrets.token_urlsafe(24)
    session = RecordingSession(
        token=token, organizer_id=current_user.id, headcount=body.headcount, status="pending"
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return SessionCreateResponse(
        session_token=session.token, sign_url=_build_sign_url(session.token), headcount=session.headcount
    )


@router.get("/sessions/{session_token}", response_model=SessionStatusResponse)
def get_session_status(
    session_token: str,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _get_owned_session(db, session_token, current_user)
    confirmed = _count_confirmed(db, session.id)
    return SessionStatusResponse(
        confirmed_count=confirmed,
        headcount=session.headcount,
        ready=confirmed >= session.headcount,
        recap_id=session.recap_id,
    )


@router.post("/sessions/{session_token}/start")
def start_session(
    session_token: str,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _get_owned_session(db, session_token, current_user)
    if session.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La session est déjà démarrée.")

    confirmed = _count_confirmed(db, session.id)
    if confirmed < session.headcount:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Signatures insuffisantes ({confirmed}/{session.headcount}).",
        )

    session.status = "started"
    db.commit()
    return {"message": "Session démarrée."}


@router.get("/sessions/{session_token}/public", response_model=PublicSessionResponse)
def get_public_session(session_token: str, request: Request, db: Session = Depends(get_db)):
    _public_status_rate_limiter.check(request.client.host, "Trop de requêtes, réessaie plus tard.")

    session = db.query(RecordingSession).filter(RecordingSession.token == session_token).first()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session introuvable.")

    confirmed = _count_confirmed(db, session.id)
    return PublicSessionResponse(
        headcount=session.headcount, confirmed_count=confirmed, status=session.status
    )


@router.post("/sessions/{session_token}/sign")
def sign_attendance(session_token: str, body: SignRequest, request: Request, db: Session = Depends(get_db)):
    _sign_ip_rate_limiter.check(request.client.host, "Trop de tentatives, réessaie plus tard.")
    _sign_session_rate_limiter.check(session_token, "Trop de signatures pour cette session.")

    session = db.query(RecordingSession).filter(RecordingSession.token == session_token).first()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session introuvable.")
    if session.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La session est clôturée, la présence n'est plus modifiable.",
        )

    signature = Signature(session_id=session.id, nom=body.nom, image_data=body.image)
    db.add(signature)
    db.commit()
    return {"message": "Présence enregistrée."}
