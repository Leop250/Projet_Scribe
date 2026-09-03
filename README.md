# Projet_Scribe — What's On Meeting

[![Backend tests](https://github.com/Leop250/Projet_Scribe/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/Leop250/Projet_Scribe/actions/workflows/backend-tests.yml)
[![codecov](https://codecov.io/gh/Leop250/Projet_Scribe/branch/develop/graph/badge.svg)](https://codecov.io/gh/Leop250/Projet_Scribe)

Projet fil rouge DATA IA3 — une application qui transforme des réunions (enregistrées au dictaphone ou rejointes automatiquement via un bot de calendrier) en comptes-rendus structurés, générés par IA.

## Fonctionnalités

- **Authentification** — inscription, vérification par code envoyé par e-mail, connexion par JWT, réinitialisation de mot de passe.
- **Enregistrement dictaphone** — upload d'un audio, transcription (Mistral), génération d'un compte-rendu structuré (résumé, thèmes, intervenants, actions) via un classifieur IA, avec une vérification de modération avant retour.
- **Comptes-rendus** — listing des recaps de l'utilisateur et consultation du détail d'un compte-rendu.
- **Présence / signatures** — sessions de présence avec signature par QR-code.
- **Bot de calendrier** — connexion à Google Calendar (OAuth) et rejoint automatique des réunions via MeetingBaaS, avec récupération du compte-rendu associé.

## Stack technique

**Backend** — Python 3.12, FastAPI, SQLAlchemy + Alembic (PostgreSQL), JWT (`python-jose`) + `passlib`/`bcrypt`, Mistral AI (speech-to-text) et Together AI (classification), Resend (e-mails transactionnels).

**Frontend** — React 19, Vite, React Router, Tailwind CSS.

**CI** — GitHub Actions (tests backend + couverture), Codecov.

## Structure du repo

```
backend/
  ai/              transcription (Mistral), classification (Together AI), modération
  auth/            inscription, connexion, vérification, JWT
  attendance/      sessions de présence, signatures
  calendar_bots/   OAuth Google Calendar, synchronisation, bot MeetingBaaS
  database/        connexion SQLAlchemy, modèles ORM (Recap)
  alembic/         migrations de base de données
  unit_testing/    tests unitaires (pytest)
  main.py          point d'entrée FastAPI

frontend/
  src/
    pages/         écrans de l'application (Auth, Record, Recap, Settings, ...)
    components/    composants réutilisables
    context/       contextes React (auth, recap)
    api/           appels au backend
```

## Installation

### Prérequis
- Python 3.12
- Node.js 18+
- Une base PostgreSQL accessible
- Des clés API : Mistral, Together AI, Resend, Google OAuth, MeetingBaaS (voir ci-dessous)

### Variables d'environnement
Copier `backend/.env.example` vers `.env` à la racine du projet et renseigner les valeurs (URL de base de données, clés IA, secrets d'authentification, configuration du bot calendrier, etc.) :

```bash
cp backend/.env.example .env
```

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sous Windows
pip install -r requirements.txt
alembic upgrade head
```

### Frontend
```bash
cd frontend
npm install
```

## Lancer le projet en développement

Le script `run.sh` démarre le backend (Uvicorn, port 8000) et le frontend (Vite, port 5173) en parallèle :

```bash
./run.sh
```

Ou séparément :
```bash
# Backend
cd backend && uvicorn main:app --reload

# Frontend
cd frontend && npm run dev
```

## Tests

Les tests unitaires du backend (hors appels IA réels, qui sont simulés) vivent dans `backend/unit_testing/` :

```bash
cd backend
pip install -r requirements-dev.txt
pytest --cov --cov-report=xml
```

Ils tournent automatiquement en CI sur chaque push/PR vers `main` et `develop` (voir `.github/workflows/backend-tests.yml`), avec remontée de la couverture sur Codecov.

## Licence

MIT — voir [LICENSE](LICENSE).
