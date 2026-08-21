from passlib.context import CryptContext
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from database import Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_DUMMY_HASH = pwd_context.hash("dummy-password-for-timing-safety")


class UserModel(Base):
    __tablename__ = "users"
    id = Column("user_id", Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_verified = Column(Boolean, nullable=False, default=False, server_default="false")
    verification_code = Column(String, nullable=True)
    verification_code_expires_at = Column(DateTime(timezone=True), nullable=True)
    participants_list_of_recaps = Column(JSONB, nullable=True, default=list)
    reset_code = Column(String, nullable=True)
    reset_code_expires_at = Column(DateTime(timezone=True), nullable=True)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(db: Session, email: str, password: str) -> UserModel | None:
    user = get_by_email(db, email)
    password_ok = verify_password(password, user.hashed_password if user else _DUMMY_HASH)
    if not user or not password_ok:
        return None
    return user


def get_by_email(db: Session, email: str) -> UserModel | None:
    return db.query(UserModel).filter(UserModel.email == email.strip().lower()).first()
