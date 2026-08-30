from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from auth import dependencies as dependencies_module
from auth.dependencies import get_current_user


def test_raises_401_when_no_token_is_provided():
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token=None, db_session=MagicMock())

    assert exc_info.value.status_code == 401


def test_raises_401_when_token_payload_has_no_subject(monkeypatch):
    monkeypatch.setattr(dependencies_module, "verify_token", lambda token: {})

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token="some-token", db_session=MagicMock())

    assert exc_info.value.status_code == 401


def test_raises_401_when_user_does_not_exist(monkeypatch):
    monkeypatch.setattr(dependencies_module, "verify_token", lambda token: {"sub": "ghost@example.com"})
    monkeypatch.setattr(dependencies_module, "get_by_email", lambda db_session, email: None)

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token="some-token", db_session=MagicMock())

    assert exc_info.value.status_code == 401


def test_raises_401_when_user_is_not_verified(monkeypatch):
    unverified_user = MagicMock(is_verified=False)
    monkeypatch.setattr(dependencies_module, "verify_token", lambda token: {"sub": "alice@example.com"})
    monkeypatch.setattr(dependencies_module, "get_by_email", lambda db_session, email: unverified_user)

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token="some-token", db_session=MagicMock())

    assert exc_info.value.status_code == 401


def test_returns_the_user_when_token_and_verification_are_valid(monkeypatch):
    verified_user = MagicMock(is_verified=True)
    monkeypatch.setattr(dependencies_module, "verify_token", lambda token: {"sub": "alice@example.com"})
    monkeypatch.setattr(dependencies_module, "get_by_email", lambda db_session, email: verified_user)

    result = get_current_user(token="some-token", db_session=MagicMock())

    assert result is verified_user
