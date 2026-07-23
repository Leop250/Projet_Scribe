# visio_to_database — notes

Le chemin que prend une réunion visio jusqu'à la base de données.

## Le chemin

```
meetingbaas_teams_bot.py (entrée)
        │
        ▼
meetingbaas_client.create_bot()          → envoie le bot "Scribe" dans la réunion (Meeting BaaS)
        │
        ▼
meetingbaas_client.wait_for_completion()  → poll le statut du bot jusqu'à la fin de la réunion
        │
        ▼
transcript.load_transcription_if_needed() → télécharge le transcript (lien S3 présigné → JSON)
        │
        ▼
transcript.extract_diarized_transcript()  → parse les utterances en segments {speaker, start, end, text}
        │
        ▼
save_meeting.save_meeting()
        │
        ├─ transcript.build_transcript_text()      → texte brut "speaker: texte"
        ├─ transcript.build_speakers_list()         → liste des intervenants
        ├─ transcript.build_meeting_name()          → nom du recap (participants humains)
        ├─ llm.generate_report()                    → résumé + thèmes + actions (Together AI)
        └─ db.SessionLocal() + models.Recap          → insert en base (source="visio")
```

## Détails par étape

- **create_bot** : POST `/v2/bots` sur l'API Meeting BaaS avec l'URL de la réunion. Mode audio_only par défaut, transcription via Gladia.
- **wait_for_completion** : poll toutes les 15s le statut du bot (`GET /v2/bots/{id}`), attend `call_ended`/`completed` + présence de l'audio, avec un délai de grâce de 5 min après la fin de la réunion.
- **load_transcription_if_needed** : le champ `transcription` de la réponse est une URL S3 présignée, pas le contenu direct → il faut la télécharger.
- **extract_diarized_transcript** : le JSON téléchargé a la forme `{"result": {"utterances": [...]}}`. Un speaker vide/"Unknown" est renommé "Inconnu".
- **save_meeting** : si aucun segment diarisé n'est trouvé, fallback sur les participants Meeting BaaS pour construire les speakers. Le `user_id` est `None` en attendant l'authentification (TODO dans le code).
- **generate_report** (llm.py) : envoie le transcript à Together AI (`Qwen/Qwen3.7-Max`) avec le prompt système `agent_context.txt`, réponse forcée en JSON (`summary`, `themes`, `actions`). Les `speakers` sont rajoutés après coup, pas générés par le LLM.
- **Recap** (models.py) : table `recaps`, colonne `source` vaut `"visio"` ici (vs `"dictaphone"` pour l'autre pipeline).

## Pour lancer

```bash
python3 meetingbaas_teams_bot.py "<url de la réunion>"
```

Variables d'env nécessaires (voir `.env.example`) : `MEETING_BAAS_API_KEY`, `GLADIA_API_KEY`, `TOGETHER_API_KEY`, `DATABASE_URL`.

## À côté : vexa_bot.py

`vexa_bot.py` est un chemin alternatif (API Vexa directe, pas Meeting BaaS) qui envoie le bot et affiche le transcript dans le terminal — mais **ne pousse pas encore en base**. Pas branché sur `save_meeting.py` pour l'instant.
