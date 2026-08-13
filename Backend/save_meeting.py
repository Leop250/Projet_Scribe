import json

from sqlalchemy import func

from llm import generate_report
from db import SessionLocal
from models import Recap, User
from transcript import (
    load_transcription_if_needed,
    extract_diarized_transcript,
    build_transcript_text,
    build_speakers_list,
    build_speakers_from_participants,
    build_meeting_name,
)


def save_meeting(bot_result: dict, bot_name: str, source: str = "visio", emails: list | None = None) -> dict:

    bot_result = load_transcription_if_needed(bot_result)
    segments = extract_diarized_transcript(bot_result)
    participants = bot_result.get("participants") or []

    if segments:
        transcript_text = build_transcript_text(segments)
        speakers_list = build_speakers_list(segments)
    else:
        transcription = bot_result.get("transcription")
        if isinstance(transcription, str) and transcription.strip():
            transcript_text = transcription
        elif transcription:
            transcript_text = json.dumps(transcription, ensure_ascii=False)
        else:
            transcript_text = "(aucune transcription disponible)"
        speakers_list = build_speakers_from_participants(participants)
        print("Aucun segment diarisé, utilisation des participants pour les speakers.")

    meeting_name = build_meeting_name(
        participants,
        bot_name=bot_name,
        fallback_name=bot_result.get("bot_name", bot_name),
    )

    report = generate_report(transcript_text)
    report["speakers"] = speakers_list

    recap = Recap(
        name=meeting_name,
        source=source,
        transcription=transcript_text,
        reporting=report,
        emails=emails or None,
    )

    db = SessionLocal()
    try:
        db.add(recap)
        db.commit()
        db.refresh(recap)
        recap_id, created_at = recap.recap_id, recap.created_at

        if emails:
            matched_users = db.query(User).filter(func.lower(User.email).in_([e.lower() for e in emails])).all()
            for user in matched_users:
                if recap_id not in (user.participants_list_of_recaps or []):
                    user.participants_list_of_recaps = (user.participants_list_of_recaps or []) + [recap_id]
            db.commit()
    finally:
        db.close()

    return {"id": recap_id, "created_at": created_at}
