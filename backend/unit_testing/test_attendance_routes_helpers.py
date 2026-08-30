from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from attendance import routes as attendance_routes
from attendance.routes import _build_sign_url, _count_confirmed, _get_owned_session, _normalize_url


def test_normalize_url_adds_https_when_missing_scheme():
    assert _normalize_url("example.com") == "https://example.com"


def test_normalize_url_keeps_existing_scheme():
    assert _normalize_url("http://example.com") == "http://example.com"
    assert _normalize_url("https://example.com") == "https://example.com"


def test_normalize_url_passes_through_empty_values():
    assert _normalize_url("") == ""
    assert _normalize_url(None) is None


def test_build_sign_url_uses_the_configured_frontend_url(monkeypatch):
    monkeypatch.setattr(attendance_routes, "FRONTEND_URL", "https://app.example.com")

    assert _build_sign_url("abc123") == "https://app.example.com/sign/abc123"


def test_get_owned_session_returns_the_session_when_owned_by_current_user():
    fake_session = MagicMock(organizer_id=42)
    fake_db = MagicMock()
    fake_db.query.return_value.filter.return_value.first.return_value = fake_session
    current_user = MagicMock(id=42)

    result = _get_owned_session(fake_db, "token-abc", current_user)

    assert result is fake_session


def test_get_owned_session_raises_404_when_session_does_not_exist():
    fake_db = MagicMock()
    fake_db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        _get_owned_session(fake_db, "token-abc", MagicMock(id=42))

    assert exc_info.value.status_code == 404


def test_get_owned_session_raises_404_when_owned_by_someone_else():
    fake_session = MagicMock(organizer_id=42)
    fake_db = MagicMock()
    fake_db.query.return_value.filter.return_value.first.return_value = fake_session
    current_user = MagicMock(id=999)

    with pytest.raises(HTTPException) as exc_info:
        _get_owned_session(fake_db, "token-abc", current_user)

    assert exc_info.value.status_code == 404


def test_count_confirmed_returns_the_signature_count():
    fake_db = MagicMock()
    fake_db.query.return_value.filter.return_value.count.return_value = 7

    assert _count_confirmed(fake_db, session_id=1) == 7
