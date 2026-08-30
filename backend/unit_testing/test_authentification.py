from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from jose import jwt

from auth.authentification import ALGORITHM, SECRET_KEY, create_access_token, verify_token


def test_create_access_token_round_trips_through_verify_token():
    token = create_access_token(data={"sub": "alice@example.com"})

    payload = verify_token(token)

    assert payload["sub"] == "alice@example.com"
    assert "exp" in payload


def test_create_access_token_sets_an_expiry_in_the_future():
    before = datetime.now(timezone.utc)
    token = create_access_token(data={"sub": "alice@example.com"})
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    assert expires_at > before


def test_verify_token_rejects_a_garbage_token():
    with pytest.raises(HTTPException) as exc_info:
        verify_token("not-a-valid-jwt")

    assert exc_info.value.status_code == 401


def test_verify_token_rejects_a_token_signed_with_a_different_key():
    forged_token = jwt.encode(
        {"sub": "alice@example.com", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        "a-different-secret",
        algorithm=ALGORITHM,
    )

    with pytest.raises(HTTPException) as exc_info:
        verify_token(forged_token)

    assert exc_info.value.status_code == 401


def test_verify_token_rejects_an_expired_token():
    expired_token = jwt.encode(
        {"sub": "alice@example.com", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    with pytest.raises(HTTPException) as exc_info:
        verify_token(expired_token)

    assert exc_info.value.status_code == 401
