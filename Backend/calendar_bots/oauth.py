"""Échange OAuth avec Google (modèle bring-your-own-credentials de MeetingBaaS :
c'est nous qui gérons ce flow, MeetingBaaS ne fait que recevoir le refresh_token final).
"""

import os
from urllib.parse import urlencode

import httpx

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
# Flow distinct de celui de l'organisateur : ici on veut juste vérifier l'identité
# du participant qui consent, pas un accès durable à son compte.
SIGNIN_SCOPE = "openid email"
# .readonly (attendu par MeetingBaaS, cf. FST_ERR_OAUTH_TOKEN_REFRESH_FAILED sans lui)
# + .events (nécessaire pour patcher l'event nous-mêmes, voir google_calendar.py).
SCOPE = "https://www.googleapis.com/auth/calendar.readonly https://www.googleapis.com/auth/calendar.events"


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


def build_signin_url(redirect_uri, state):
    params = {
        "client_id": os.environ["GOOGLE_OAUTH_CLIENT_ID"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": SIGNIN_SCOPE,
        "state": state,
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def get_verified_email(code, redirect_uri):
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
    id_token = response.json()["id_token"]

    # On revérifie le id_token auprès de Google plutôt que de le décoder nous-mêmes :
    # évite d'ajouter une dépendance de vérification de signature JWT pour ce seul usage.
    verify = httpx.get(GOOGLE_TOKENINFO_URL, params={"id_token": id_token}, timeout=30)
    verify.raise_for_status()
    claims = verify.json()

    if claims.get("aud") != os.environ["GOOGLE_OAUTH_CLIENT_ID"]:
        raise RuntimeError("id_token non destiné à cette application.")
    if claims.get("email_verified") != "true":
        raise RuntimeError("Adresse e-mail Google non vérifiée.")
    return claims["email"]


def get_access_token(refresh_token):
    response = httpx.post(
        GOOGLE_TOKEN_URL,
        data={
            "refresh_token": refresh_token,
            "client_id": os.environ["GOOGLE_OAUTH_CLIENT_ID"],
            "client_secret": os.environ["GOOGLE_OAUTH_CLIENT_SECRET"],
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]
