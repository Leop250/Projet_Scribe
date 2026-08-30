"""Configuration partagée pour les tests unitaires du backend.

Ce module fait deux choses avant que le moindre test ne s'exécute :

1. Il ajoute le dossier `backend/` au `sys.path` et s'y place comme dossier
   courant, pour que les imports absolus utilisés partout dans le code
   (`from database.database import ...`, `from auth.users import ...`, etc.)
   fonctionnent exactement comme lorsque l'app est lancée avec
   `uvicorn main:app` depuis `backend/`.
2. Il fixe des valeurs factices pour toutes les variables d'environnement
   requises à l'import des modules (clé JWT, URL de base de données, clés
   des services externes...), afin que les tests puissent tourner sans
   `.env` réel ni accès réseau. `setdefault` est utilisé partout : si une
   vraie valeur est déjà présente dans l'environnement, elle n'est pas
   écrasée.

Aucun de ces modules n'est appelé pour de vrai pendant les tests (les
dépendances externes — base de données, IA, envoi d'e-mail — sont
remplacées par des doublures de test / mocks) : ces valeurs ne servent
qu'à satisfaire les imports.
"""

import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.chdir(BACKEND_DIR)

_DEFAULT_TEST_ENV = {
    "SECRET_KEY": "unit-testing-secret-key",
    "ALGORITHM": "HS256",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
    "EMAIL_VERIFICATION_EXPIRE_MINUTES": "15",
    "DATABASE_URL": "sqlite:///:memory:",
    "FRONTEND_URL": "http://localhost:5173",
    "RESEND_API_KEY": "test-resend-key",
    "EMAIL": "Test <test@example.com>",
    # Ces deux-là ne servent qu'à permettre l'import de main.py (qui importe
    # ai.classifier / ai.speech_to_text) — aucun appel réel n'est fait
    # pendant les tests unitaires du backend.
    "MISTRAL_API_KEY": "test-mistral-key",
    "TOGETHER_API_KEY": "test-together-key",
    "CLASSIFIER_MODEL": "test-classifier-model",
    "SPEECH_TO_TEXT_MODEL": "test-speech-to-text-model",
}

for _key, _value in _DEFAULT_TEST_ENV.items():
    os.environ.setdefault(_key, _value)
