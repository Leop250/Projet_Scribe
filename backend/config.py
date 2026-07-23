"""
config.py
---------
Charge les clés API du projet depuis les variables d'environnement.

Toutes les clés doivent être définies soit :
  - dans un vrai fichier .env à la racine du projet (voir .env.example) :
        VEXA_API_KEY=vx_sk_...
        MEETING_BAAS_API_KEY=...
        GLADIA_API_KEY=...
  - soit exportées manuellement dans le shell.

Le fichier .env est ignoré par git (voir .gitignore) : ne jamais y toucher.
"""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()  # charge automatiquement le .env à la racine s'il existe
except ImportError:
    pass


def get_api_key(env_var: str) -> str:
    """Récupère une clé API depuis les variables d'environnement.

    Args:
        env_var: nom de la variable d'environnement (ex: "VEXA_API_KEY").

    Raises:
        EnvironmentError si la clé n'est pas définie.
    """
    api_key = os.environ.get(env_var)
    if not api_key:
        raise EnvironmentError(
            f"La clé API {env_var} n'est pas définie. "
            f"Ajoute-la dans ton fichier .env (voir .env.example) "
            f"ou exporte-la manuellement : export {env_var}=\"...\""
        )
    return api_key


def get_vexa_api_key() -> str:
    return get_api_key("VEXA_API_KEY")


def get_meeting_baas_api_key() -> str:
    return get_api_key("MEETING_BAAS_API_KEY")


def get_gladia_api_key() -> str:
    return get_api_key("GLADIA_API_KEY")

def get_together_api_key() -> str:
    return get_api_key("TOGETHER_API_KEY")


def get_database_url() -> str:
    return get_api_key("DATABASE_URL")