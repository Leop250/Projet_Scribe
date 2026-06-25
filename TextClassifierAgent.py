import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()


class TextClassifierAgent:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=self.api_key)  # mot-clé api_key, pas positionnel

    def classify_text(self, reunion_content):
        system_context = (
            "Tu es un assistant expert en analyse de données textuelles. Ton rôle est de classifier "
            "le compte-rendu ou la transcription d'une réunion qui te sera fournie par l'utilisateur.\n\n"
            "Tu dois analyser le texte et retourner obligatoirement un objet JSON contenant les clés suivantes :\n"
            "- 'categorie_principale': Le thème principal (ex: Technique, Commercial, RH, Stratégie, Rétrospective).\n"
            "- 'resume_court': Un résumé en 2 phrases max du contenu.\n"
            "- 'actions_cles': Une liste des décisions prises ou des tâches à accomplir.\n"
            "- 'sentiment_general': Le ton de la réunion (ex: Positif/Productif, Tendu, Neutre).\n\n"
            "Réponds UNIQUEMENT avec le bloc JSON, sans texte avant ni après."
        )

        completion = self.client.chat.completions.create(
            model="qwen/qwen3-32b",
            reasoning_format="hidden",                  # masque les balises de raisonnement
            response_format={"type": "json_object"},    # force un JSON valide
            messages=[
                {"role": "system", "content": system_context},
                {
                    "role": "user",
                    "content": f"Voici le contenu de la réunion à classifier : {reunion_content}",
                },
            ],
        )

        content = completion.choices[0].message.content
        print(content)
        try:
            return json.loads(content)  # renvoie un vrai dictionnaire
        except json.JSONDecodeError:
            return content  # repli : on renvoie la chaîne brute