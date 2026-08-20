"""Appels directs à l'API Google Calendar (v3), en dehors de MeetingBaaS.

Nécessaire car l'API Calendar de MeetingBaaS est en lecture seule sur les
événements : pour y insérer le lien de consentement, il faut passer par
l'API Google elle-même, avec le refresh_token obtenu lors du flow OAuth.
"""

import httpx

from . import oauth

BASE_URL = "https://www.googleapis.com/calendar/v3"


def add_consent_redirect(refresh_token, google_calendar_id, google_event_id, redirect_url):
    access_token = oauth.get_access_token(refresh_token)
    response = httpx.patch(
        f"{BASE_URL}/calendars/{google_calendar_id}/events/{google_event_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"location": redirect_url},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()
