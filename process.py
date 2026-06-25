from SpeechToTextAgent import SpeechToTextAgent
from TextClassifierAgent import TextClassifierAgent


def main():
    speech_to_text_agent = SpeechToTextAgent()     
    text_classifier_agent = TextClassifierAgent()    

    meeting_content = speech_to_text_agent.transcribe_meeting(
        "https://meet.google.com/uoj-gwbf-imm"
    )
    classification_result = text_classifier_agent.classify_text(meeting_content)
    print("Classification Result:", classification_result)


if __name__ == "__main__":
    main()