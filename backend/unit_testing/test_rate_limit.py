import pytest
from fastapi import HTTPException

from rate_limit import RateLimiter, _PURGE_THRESHOLD


def test_allows_requests_under_the_limit():
    limiter = RateLimiter(window_seconds=60, max_attempts=3)

    for _ in range(3):
        limiter.check("client-1", "trop de tentatives")  # ne doit pas lever


def test_blocks_once_the_limit_is_reached():
    limiter = RateLimiter(window_seconds=60, max_attempts=2)

    limiter.check("client-1", "trop de tentatives")
    limiter.check("client-1", "trop de tentatives")

    with pytest.raises(HTTPException) as exc_info:
        limiter.check("client-1", "trop de tentatives")

    assert exc_info.value.status_code == 429
    assert exc_info.value.detail == "trop de tentatives"


def test_keys_are_tracked_independently():
    limiter = RateLimiter(window_seconds=60, max_attempts=1)

    limiter.check("client-1", "trop de tentatives")
    limiter.check("client-2", "trop de tentatives")  # autre clé, doit passer

    with pytest.raises(HTTPException):
        limiter.check("client-1", "trop de tentatives")
    with pytest.raises(HTTPException):
        limiter.check("client-2", "trop de tentatives")


def test_old_attempts_expire_after_the_window(monkeypatch):
    current_time = [1_000.0]
    monkeypatch.setattr("rate_limit.time", lambda: current_time[0])

    limiter = RateLimiter(window_seconds=10, max_attempts=1)

    limiter.check("client-1", "trop de tentatives")
    with pytest.raises(HTTPException):
        limiter.check("client-1", "trop de tentatives")

    # On avance le temps au-delà de la fenêtre : la tentative expirée
    # ne doit plus compter.
    current_time[0] += 11
    limiter.check("client-1", "trop de tentatives")  # ne doit pas lever


def test_purge_expired_removes_only_stale_keys():
    limiter = RateLimiter(window_seconds=10, max_attempts=5)
    now = 1_000.0

    limiter._attempts["stale"] = [now - 100]
    limiter._attempts["fresh"] = [now - 1]
    limiter._attempts["empty"] = []

    limiter._purge_expired(now)

    assert "stale" not in limiter._attempts
    assert "empty" not in limiter._attempts
    assert "fresh" in limiter._attempts


def test_purge_is_triggered_once_the_key_count_exceeds_threshold(monkeypatch):
    monkeypatch.setattr("rate_limit._PURGE_THRESHOLD", 2)
    current_time = [1_000.0]
    monkeypatch.setattr("rate_limit.time", lambda: current_time[0])

    limiter = RateLimiter(window_seconds=10, max_attempts=5)

    limiter.check("client-1", "x")
    current_time[0] += 100  # cette entrée sera périmée au moment du purge
    limiter.check("client-2", "x")
    limiter.check("client-3", "x")  # dépasse le seuil abaissé -> déclenche _purge_expired

    assert "client-1" not in limiter._attempts


def test_purge_threshold_constant_is_a_thousand():
    # Garde-fou : si la constante change sans intention, ce test le signale.
    assert _PURGE_THRESHOLD == 1000
