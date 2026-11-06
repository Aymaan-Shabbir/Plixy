from utils.audio_processor import process_input
from core.transcriber import transcribe_all

if __name__ == "__main__":

    source = input("Enter YouTube URL or local audio path: ").strip()
    language = input("Enter language (english/hinglish): ").strip().lower() 

    if not source:
        raise ValueError("Input cannot be empty")

    chunks = process_input(source)

    doc = transcribe_all(chunks,language)

    print("\n===== TRANSCRIPTION =====\n")
    print(doc)
    