import os
from pathlib import Path

import resend
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

_BASE_DIR = Path(__file__).resolve().parent
load_dotenv(_BASE_DIR.parent / ".env")

resend.api_key = os.environ["RESEND_API_KEY"]
EMAIL = os.environ.get("EMAIL", "Scribe <login@tondomaine.com>")

_jinja_env = Environment(loader=FileSystemLoader(_BASE_DIR), autoescape=True)
_template = _jinja_env.get_template("scribe-login-email.html")


def render_verification_email(code: str) -> str:
    return _template.render(code=code)


def render_password_reset_email(code: str) -> str:
    return _template.render(
        code=code,
        badge="Réinitialisation du mot de passe",
        title="Réinitialise<br>ton mot de passe",
        intro="Recopie ce code sur Scribe pour choisir un nouveau mot de passe :",
    )


async def _send_email_async(to: str, subject: str, html: str) -> dict:
    params: resend.Emails.SendParams = {
        "from": EMAIL,
        "to": [to],
        "subject": subject,
        "html": html,
    }
    return await resend.Emails.send_async(params)


async def send_verification_code_email_async(to: str, code: str) -> dict:
    html = render_verification_email(code)
    return await _send_email_async(to, "Ton code de vérification — Scribe", html)


async def send_password_reset_email_async(to: str, code: str) -> dict:
    html = render_password_reset_email(code)
    return await _send_email_async(to, "Réinitialise ton mot de passe — Scribe", html)
