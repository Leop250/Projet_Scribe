import os

try:
    from dotenv import load_dotenv
    load_dotenv()  # charge automatiquement le .env à la racine s'il existe
except ImportError:
    pass


def get_api_key(env_var: str) -> str:
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