"""Échange OAuth avec Google (modèle bring-your-own-credentials de MeetingBaaS :
c'est nous qui gérons ce flow, MeetingBaaS ne fait que recevoir le refresh_token final).
"""

import os
from urllib.parse import urlencode

import httpx

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/calendar.readonly"


def build_authorize_url(redirect_uri, state):
    params = {
        "client_id": os.environ["GOOGLE_OAUTH_CLIENT_ID"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": SCOPE,
        # access_type=offline + prompt=consent : indispensables pour obtenir un
        # refresh_token à chaque autorisation (sinon Google n'en renvoie un qu'une fois).
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def exchange_code_for_refresh_token(code, redirect_uri):
    response = httpx.post(
        GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": os.environ["GOOGLE_OAUTH_CLIENT_ID"],
            "client_secret": os.environ["GOOGLE_OAUTH_CLIENT_SECRET"],
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=30,
    )
    response.raise_for_status()
    refresh_token = response.json().get("refresh_token")
    if not refresh_token:
        raise RuntimeError(
            "Google n'a pas renvoyé de refresh_token. L'utilisateur a probablement déjà "
            "autorisé cette app par le passé : révoque l'accès sur "
            "https://myaccount.google.com/permissions puis relance le flow."
        )
    return refresh_token
