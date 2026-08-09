import re
from typing import Annotated, TypeAlias

from pydantic import BaseModel, BeforeValidator, EmailStr, Field, field_validator


def _normalize_email(v: str) -> str:
    return v.strip().lower()


NormalizedEmail: TypeAlias = Annotated[EmailStr, BeforeValidator(_normalize_email)]
VerificationCode: TypeAlias = Annotated[str, Field(min_length=6, max_length=6, pattern=r"^\d{6}$")]


class Token(BaseModel):
    access_token: str
    token_type: str


class VerifyCodeRequest(BaseModel):
    email: NormalizedEmail
    code: VerificationCode


class ResendCodeRequest(BaseModel):
    email: NormalizedEmail


class ForgotPasswordRequest(BaseModel):
    email: NormalizedEmail


def _check_password_strength(v: str) -> str:
    if len(v.encode("utf-8")) > 72:
        raise ValueError("Le mot de passe ne doit pas dépasser 72 caractères.")
    if len(v) < 8 or not re.search(r"[A-Z]", v) or not re.search(r"[^A-Za-z0-9]", v):
        raise ValueError(
            "Le mot de passe doit contenir au moins 8 caractères, une majuscule et un caractère spécial."
        )
    return v


class ResetPasswordRequest(BaseModel):
    email: NormalizedEmail
    code: VerificationCode
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _check_password_strength(v)


class UserRegister(BaseModel):
    username: Annotated[str, Field(min_length=1, max_length=50)]
    email: NormalizedEmail
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _check_password_strength(v)


class UserVerification(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_verified: bool

    class Config:
        from_attributes = True
