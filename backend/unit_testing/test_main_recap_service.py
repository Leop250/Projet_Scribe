from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

import main
from main import RecapService


# --- normalize_url -----------------------------------------------------------


def test_normalize_url_adds_https_when_missing_scheme():
    assert RecapService.normalize_url("example.com") == "https://example.com"


def test_normalize_url_keeps_existing_scheme():
    assert RecapService.normalize_url("http://example.com") == "http://example.com"


def test_normalize_url_passes_through_falsy_values():
    assert RecapService.normalize_url("") == ""


# --- add_recap_to_user --------------------------------------------------------


def test_add_recap_to_user_starts_a_new_list_when_user_has_none():
    user = MagicMock(participants_list_of_recaps=None)

    RecapService.add_recap_to_user(user, 5)

    assert user.participants_list_of_recaps == [5]


def test_add_recap_to_user_appends_without_mutating_the_original_list():
    original = [1, 2]
    user = MagicMock(participants_list_of_recaps=original)

    RecapService.add_recap_to_user(user, 3)

    assert user.participants_list_of_recaps == [1, 2, 3]
    assert original == [1, 2]  # la liste d'origine n'est pas modifiée en place


# --- create_recap --------------------------------------------------------------


def test_create_recap_persists_and_returns_the_recap():
    fake_db = MagicMock()

    recap = RecapService.create_recap(
        fake_db, emails="a@b.com", name="reunion.wav", transcript="bonjour", report={"summary": "ok"}
    )

    assert recap.emails == "a@b.com"
    assert recap.name == "reunion.wav"
    assert recap.source == "dictaphone"
    assert recap.transcription == "bonjour"
    assert recap.reporting == {"summary": "ok"}
    fake_db.add.assert_called_once_with(recap)
    fake_db.commit.assert_called_once()
    fake_db.refresh.assert_called_once_with(recap)


# --- attach_participants -------------------------------------------------------


def test_attach_participants_links_known_users_and_commits_once(monkeypatch):
    known_users = {"a@b.com": MagicMock(participants_list_of_recaps=[])}
    monkeypatch.setattr(main, "get_by_email", lambda db_session, email: known_users.get(email))
    fake_db = MagicMock()

    RecapService.attach_participants(fake_db, "a@b.com,ghost@b.com", recap_id=42)

    assert known_users["a@b.com"].participants_list_of_recaps == [42]
    fake_db.commit.assert_called_once()


def test_attach_participants_does_nothing_for_unknown_emails(monkeypatch):
    monkeypatch.setattr(main, "get_by_email", lambda db_session, email: None)
    fake_db = MagicMock()

    RecapService.attach_participants(fake_db, "ghost@b.com", recap_id=42)

    fake_db.commit.assert_called_once()  # toujours appelé, même sans rattachement


# --- list_summaries -------------------------------------------------------------


def test_list_summaries_maps_recaps_and_falls_back_on_missing_reporting_fields():
    # `name` est un kwarg réservé par MagicMock (nom interne du mock) : il faut
    # l'assigner après coup pour que ça devienne un vrai attribut `.name`.
    recap = MagicMock(recap_id=1, source="dictaphone", created_at="2026-08-29T10:00:00Z", reporting=None)
    recap.name = "reunion.wav"
    fake_db = MagicMock()
    fake_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [recap]

    summaries = RecapService.list_summaries(fake_db, [1])

    assert len(summaries) == 1
    summary = summaries[0]
    assert summary.id == 1
    assert summary.summary is None
    assert summary.themes == []
    assert summary.speaker_count is None


def test_list_summaries_reads_values_from_reporting_when_present():
    recap = MagicMock(
        recap_id=2,
        source="dictaphone",
        created_at="2026-08-29T11:00:00Z",
        reporting={"summary": "résumé", "themes": ["budget"], "speaker_count": 3},
    )
    recap.name = "reunion2.wav"
    fake_db = MagicMock()
    fake_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [recap]

    summary = RecapService.list_summaries(fake_db, [2])[0]

    assert summary.summary == "résumé"
    assert summary.themes == ["budget"]
    assert summary.speaker_count == 3


# --- get_detail ------------------------------------------------------------------


def test_get_detail_raises_404_when_recap_is_not_in_the_users_list():
    current_user = MagicMock(participants_list_of_recaps=[1, 2])

    with pytest.raises(HTTPException) as exc_info:
        RecapService.get_detail(MagicMock(), recap_id=99, current_user=current_user)

    assert exc_info.value.status_code == 404


def test_get_detail_raises_404_when_the_recap_no_longer_exists_in_db():
    current_user = MagicMock(participants_list_of_recaps=[1])
    fake_db = MagicMock()
    fake_db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        RecapService.get_detail(fake_db, recap_id=1, current_user=current_user)

    assert exc_info.value.status_code == 404


def test_get_detail_returns_the_full_response_on_success():
    current_user = MagicMock(participants_list_of_recaps=[1])
    recap = MagicMock(
        recap_id=1,
        source="dictaphone",
        created_at="2026-08-29T10:00:00Z",
        reporting={
            "summary": "résumé",
            "speaker_count": 2,
            "speakers": ["Alice", "Bob"],
            "themes": ["budget"],
            "actions": ["envoyer le compte-rendu"],
            "transcript": [{"speaker": "Alice", "text": "bonjour"}],
        },
    )
    recap.name = "reunion.wav"
    fake_db = MagicMock()
    fake_db.query.return_value.filter.return_value.first.return_value = recap

    detail = RecapService.get_detail(fake_db, recap_id=1, current_user=current_user)

    assert detail.id == 1
    assert detail.summary == "résumé"
    assert detail.speakers == ["Alice", "Bob"]
    assert detail.actions == ["envoyer le compte-rendu"]


# --- transcribe_and_classify (avec l'IA remplacée par des doublures) ------------


def test_transcribe_and_classify_deletes_the_temp_file_even_on_failure(tmp_path, monkeypatch):
    temp_file = tmp_path / "audio.wav"
    temp_file.write_bytes(b"fake-audio")

    monkeypatch.setattr(main, "call_speech_to_text_agent", MagicMock(side_effect=RuntimeError("boom")))

    with pytest.raises(RuntimeError):
        RecapService.transcribe_and_classify(temp_file)

    assert not temp_file.exists()


def test_transcribe_and_classify_returns_transcript_and_report(tmp_path, monkeypatch):
    temp_file = tmp_path / "audio.wav"
    temp_file.write_bytes(b"fake-audio")

    monkeypatch.setattr(main, "call_speech_to_text_agent", MagicMock(return_value="bonjour tout le monde"))
    monkeypatch.setattr(main, "call_classifier", MagicMock(return_value={"summary": "ok"}))

    transcript, report = RecapService.transcribe_and_classify(temp_file)

    assert transcript == "bonjour tout le monde"
    assert report == {"summary": "ok"}
    assert not temp_file.exists()
