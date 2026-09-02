"""Sauvegarde en base d'un recap produit par un bot MeetingBaaS (réunion visio)."""

import json

from sqlalchemy import func

from ai.classifier import call_classifier
from ai.moderation import verify_report
from auth.users import UserModel
from database.database import SessionLocal
from database.models import Recap

from .transcript import (
    build_meeting_name,
    build_speakers_from_participants,
    build_speakers_list,
    build_transcript_text,
    extract_diarized_transcript,
    load_transcription_if_needed,
)


def _build_transcript(bot_result: dict):
    segments = extract_diarized_transcript(bot_result)
    participants = bot_result.get("participants") or []

    if segments:
        transcript_text = build_transcript_text(segments)
        speakers_list = build_speakers_list(segments)
        return transcript_text, speakers_list, participants

    transcription = bot_result.get("transcription")
    if isinstance(transcription, str) and transcription.strip():
        transcript_text = transcription
    elif transcription:
        transcript_text = json.dumps(transcription, ensure_ascii=False)
    else:
        transcript_text = "(aucune transcription disponible)"
    speakers_list = build_speakers_from_participants(participants)
    return transcript_text, speakers_list, participants


def _link_participants(session, recap_id: int, emails: list[str]) -> None:
    if not emails:
        return
    lowered = [email.strip().lower() for email in emails if email and email.strip()]
    if not lowered:
        return
    matched_users = session.query(UserModel).filter(func.lower(UserModel.email).in_(lowered)).all()
    for user in matched_users:
        current = user.participants_list_of_recaps or []
        if recap_id not in current:
            user.participants_list_of_recaps = current + [recap_id]


def save_meeting(
    bot_result: dict,
    bot_name: str,
    source: str = "visio",
    emails: list[str] | None = None,
) -> dict:
    bot_result = load_transcription_if_needed(bot_result)
    transcript_text, speakers_list, participants = _build_transcript(bot_result)

    meeting_name = build_meeting_name(
        participants,
        bot_name=bot_name,
        fallback_name=bot_result.get("bot_name", bot_name),
    )

    report = call_classifier(transcript_text)
    report = verify_report(transcript_text, report)
    report["speakers"] = speakers_list

    recap = Recap(
        name=meeting_name,
        source=source,
        transcription=transcript_text,
        reporting=report,
        emails=",".join(emails) if emails else "",
    )

    session = SessionLocal()
    try:
        session.add(recap)
        session.commit()
        session.refresh(recap)
        recap_id, created_at = recap.recap_id, recap.created_at
        _link_participants(session, recap_id, emails or [])
        session.commit()
    finally:
        session.close()

    return {"id": recap_id, "created_at": created_at}
