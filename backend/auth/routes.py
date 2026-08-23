import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database.database import get_db
from rate_limit import RateLimiter

from .authentification import create_access_token
from .config import settings
from .dependencies import get_current_user
from .email_services import send_password_reset_email_async, send_verification_code_email_async
from .schemas import (
    ForgotPasswordRequest,
    ResendCodeRequest,
    ResetPasswordRequest,
    Token,
    UserRegister,
    UserVerification,
    VerifyCodeRequest,
)
from .users import UserModel, authenticate_user, get_by_email, get_password_hash

_signup_rate_limiter = RateLimiter(window_seconds=3600, max_attempts=5)
_login_rate_limiter = RateLimiter(window_seconds=900, max_attempts=10)
_exists_rate_limiter = RateLimiter(window_seconds=3600, max_attempts=20)
_verify_code_rate_limiter = RateLimiter(window_seconds=900, max_attempts=8)
_resend_code_rate_limiter = RateLimiter(window_seconds=3600, max_attempts=5)
_forgot_password_rate_limiter = RateLimiter(window_seconds=3600, max_attempts=5)
_reset_password_rate_limiter = RateLimiter(window_seconds=900, max_attempts=8)


def _generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _unique_username(db_session: Session, base: str) -> str:
    username = base
    suffix = 0
    while db_session.query(UserModel).filter(UserModel.username == username).first():
        suffix += 1
        username = f"{base}{suffix}"
    return username


def _issue_token(user: UserModel) -> dict:
    return {"access_token": create_access_token(data={"sub": user.email}), "token_type": "bearer"}


def _check_code(user: UserModel | None, code: str, code_attr: str, expires_attr: str) -> None:
    stored_code = getattr(user, code_attr, None)
    expires_at = getattr(user, expires_attr, None)
    if (
        not user
        or not stored_code
        or not expires_at
        or datetime.now(timezone.utc) > expires_at
        or not secrets.compare_digest(stored_code, code)
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code invalide ou expiré.")


router = APIRouter()


@router.post("/token", response_model=Token)
def login_for_access_token(
    request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db_session: Session = Depends(get_db)
):
    _login_rate_limiter.check(
        request.client.host, "Trop de tentatives de connexion, réessaie dans quelques minutes."
    )
    user = authenticate_user(db_session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Adresse email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte non vérifié — entre le code reçu par e-mail.",
        )
    return _issue_token(user)


@router.get("/auth/session", response_model=UserVerification)
def get_session(current_user: UserModel = Depends(get_current_user)):
    return current_user


@router.get("/users/exists")
def user_exists(email: str, request: Request, db_session: Session = Depends(get_db)):
    _exists_rate_limiter.check(request.client.host, "Trop de vérifications, réessaie plus tard.")
    return {"exists": get_by_email(db_session, email) is not None}


@router.post("/users/createUsers")
async def create_user(user: UserRegister, request: Request, db_session: Session = Depends(get_db)):
    _signup_rate_limiter.check(
        request.client.host, "Trop de tentatives d'inscription depuis cette adresse, réessaie plus tard."
    )

    if get_by_email(db_session, user.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="L'email est déjà existante !",
        )

    hashed_password = get_password_hash(user.password)
    code = _generate_code()

    new_user = UserModel(
        username=_unique_username(db_session, user.username),
        email=user.email,
        hashed_password=hashed_password,
        verification_code=code,
        verification_code_expires_at=datetime.now(timezone.utc)
        + timedelta(minutes=settings.EMAIL_VERIFICATION_EXPIRE_MINUTES),
    )

    db_session.add(new_user)
    try:
        db_session.flush()
    except IntegrityError:
        db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Impossible de créer le compte, réessaie.",
        )

    try:
        await send_verification_code_email_async(to=new_user.email, code=code)
    except Exception:
        db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Impossible d'envoyer l'e-mail de vérification, réessaie.",
        )

    db_session.commit()
    db_session.refresh(new_user)

    return {"message": "Compte créé — entre le code reçu par e-mail pour l'activer.", "user_id": new_user.id}


@router.post("/auth/verify-code", response_model=Token)
def verify_code(body: VerifyCodeRequest, db_session: Session = Depends(get_db)):
    _verify_code_rate_limiter.check(body.email, "Trop de tentatives, redemande un code.")

    user = get_by_email(db_session, body.email)
    _check_code(user, body.code, "verification_code", "verification_code_expires_at")

    user.is_verified = True
    user.verification_code = None
    user.verification_code_expires_at = None
    db_session.commit()

    return _issue_token(user)


@router.post("/auth/resend-code")
async def resend_code(body: ResendCodeRequest, db_session: Session = Depends(get_db)):
    _resend_code_rate_limiter.check(body.email, "Trop de renvois, réessaie plus tard.")

    user = get_by_email(db_session, body.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compte introuvable.")
    if user.is_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ce compte est déjà vérifié.")

    code = _generate_code()
    user.verification_code = code
    user.verification_code_expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.EMAIL_VERIFICATION_EXPIRE_MINUTES
    )

    try:
        await send_verification_code_email_async(to=user.email, code=code)
    except Exception:
        db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Impossible d'envoyer l'e-mail, réessaie.",
        )

    db_session.commit()
    return {"message": "Nouveau code envoyé."}


@router.post("/auth/forgot-password")
async def forgot_password(
    body: ForgotPasswordRequest, request: Request, db_session: Session = Depends(get_db)
):
    _forgot_password_rate_limiter.check(request.client.host, "Trop de demandes, réessaie plus tard.")

    user = get_by_email(db_session, body.email)
    if user and user.is_verified:
        code = _generate_code()
        user.reset_code = code
        user.reset_code_expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.EMAIL_VERIFICATION_EXPIRE_MINUTES
        )

        try:
            await send_password_reset_email_async(to=user.email, code=code)
        except Exception:
            db_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Impossible d'envoyer l'e-mail, réessaie.",
            )

        db_session.commit()

    return {"message": "Si un compte existe et est vérifié, un code de réinitialisation a été envoyé."}


@router.post("/auth/reset-password", response_model=Token)
def reset_password(body: ResetPasswordRequest, db_session: Session = Depends(get_db)):
    _reset_password_rate_limiter.check(body.email, "Trop de tentatives, redemande un code.")

    user = get_by_email(db_session, body.email)
    _check_code(user, body.code, "reset_code", "reset_code_expires_at")

    user.hashed_password = get_password_hash(body.new_password)
    user.reset_code = None
    user.reset_code_expires_at = None
    db_session.commit()

    return _issue_token(user)
