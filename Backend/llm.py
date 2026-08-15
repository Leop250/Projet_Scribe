import json
from groq import Groq


class ReportGenerator:
    def __init__(self, context_path="agent_context.txt", model="openai/gpt-oss-20b"):
        self.client = Groq()
        self.model = model
        with open(context_path, "r") as context_file:
            self.context = context_file.read()

    def generate_report(self, transcript):
        chat_completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.context},
                {"role": "user", "content": transcript}
            ],
            temperature=0,
            max_completion_tokens=4096,
            top_p=0.95,
            stream=False,
            response_format={"type": "json_object"},
            reasoning_format="hidden",
            reasoning_effort="medium"
        )

        return json.loads(chat_completion.choices[0].message.content)


_default_report_generator = ReportGenerator()


def generate_report(transcript):
    return _default_report_generator.generate_report(transcript)
