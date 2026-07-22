import os
import json
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def save_recap(user_id, name, source, transcription, reporting):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO recaps (user_id, name, source, transcription, reporting)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, created_at;
                """,
                (user_id, name, source, transcription, json.dumps(reporting)),
            )
            row = cur.fetchone()
            conn.commit()
            return {"id": row[0], "created_at": row[1]}
    finally:
        conn.close()