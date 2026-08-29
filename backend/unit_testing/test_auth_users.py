from unittest.mock import MagicMock

from auth import users as users_module
from auth.users import (
    UserModel,
    authenticate_user,
    get_by_email,
    get_password_hash,
    verify_password,
)


def test_password_hash_round_trip():
    hashed = get_password_hash("Sup3r$ecret")

    assert hashed != "Sup3r$ecret"  # jamais stocké en clair
    assert verify_password("Sup3r$ecret", hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_get_by_email_normalizes_and_filters_on_the_lowercased_stripped_email():
    fake_query = MagicMock()
    fake_db = MagicMock()
    fake_db.query.return_value = fake_query
    fake_query.filter.return_value.first.return_value = "the-user"

    result = get_by_email(fake_db, "  Alice@Example.COM  ")

    fake_db.query.assert_called_once_with(UserModel)
    filter_expression = fake_query.filter.call_args[0][0]
    assert filter_expression.right.value == "alice@example.com"
    assert result == "the-user"


def test_authenticate_user_returns_none_when_user_does_not_exist(monkeypatch):
    monkeypatch.setattr(users_module, "get_by_email", lambda db_session, email: None)

    result = authenticate_user(MagicMock(), "ghost@example.com", "whatever")

    assert result is None


def test_authenticate_user_returns_none_on_wrong_password(monkeypatch):
    fake_user = MagicMock(hashed_password=get_password_hash("correct-password"))
    monkeypatch.setattr(users_module, "get_by_email", lambda db_session, email: fake_user)

    result = authenticate_user(MagicMock(), "alice@example.com", "wrong-password")

    assert result is None


def test_authenticate_user_returns_the_user_on_correct_password(monkeypatch):
    fake_user = MagicMock(hashed_password=get_password_hash("correct-password"))
    monkeypatch.setattr(users_module, "get_by_email", lambda db_session, email: fake_user)

    result = authenticate_user(MagicMock(), "alice@example.com", "correct-password")

    assert result is fake_user
