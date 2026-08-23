from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database.database import get_db

from .authentification import verify_token
from .users import UserModel, get_by_email

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme), db_session: Session = Depends(get_db)
) -> UserModel:
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Non authentifié",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = verify_token(token)
    email = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Non authentifié",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = get_by_email(db_session, email)
    if user is None or not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Non authentifié",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
