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


class MeetingSaver:
    def _build_transcript(self, bot_result: dict):
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

        return transcript_text, speakers_list, participants

    def save_meeting(self, bot_result: dict, bot_name: str, source: str = "visio", emails: list | None = None) -> dict:
        bot_result = load_transcription_if_needed(bot_result)
        transcript_text, speakers_list, participants = self._build_transcript(bot_result)

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

        session = SessionLocal()
        try:
            session.add(recap)
            session.commit()
            session.refresh(recap)
            recap_id, created_at = recap.recap_id, recap.created_at

            if emails:
                matched_users = session.query(User).filter(func.lower(User.email).in_([email.lower() for email in emails])).all()
                for user in matched_users:
                    if recap_id not in (user.participants_list_of_recaps or []):
                        user.participants_list_of_recaps = (user.participants_list_of_recaps or []) + [recap_id]
                session.commit()
        finally:
            session.close()

        return {"id": recap_id, "created_at": created_at}


_default_meeting_saver = MeetingSaver()


def save_meeting(bot_result: dict, bot_name: str, source: str = "visio", emails: list | None = None) -> dict:
    return _default_meeting_saver.save_meeting(bot_result, bot_name, source=source, emails=emails)
