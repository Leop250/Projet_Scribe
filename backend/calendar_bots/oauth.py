"""Échange OAuth avec Google (modèle bring-your-own-credentials de MeetingBaaS :
c'est nous qui gérons ce flow, MeetingBaaS ne fait que recevoir le refresh_token final).
"""

import os
from urllib.parse import urlencode

import httpx

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
SCOPE = "openid email https://www.googleapis.com/auth/calendar.readonly"


def build_authorize_url(redirect_uri: str, state: str) -> str:
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


def exchange_code_for_tokens(code: str, redirect_uri: str) -> dict:
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
    tokens = response.json()
    if not tokens.get("refresh_token"):
        raise RuntimeError(
            "Google n'a pas renvoyé de refresh_token. L'utilisateur a probablement déjà "
            "autorisé cette app par le passé : révoque l'accès sur "
            "https://myaccount.google.com/permissions puis relance le flow."
        )
    return tokens


def fetch_google_email(access_token: str) -> str | None:
    try:
        response = httpx.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15,
        )
        response.raise_for_status()
        return response.json().get("email")
    except httpx.HTTPError:
        return None
