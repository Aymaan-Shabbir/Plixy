
import os
import yt_dlp
from pydub import AudioSegment

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# STEP 1: Download YouTube audio as MP3
def download_youtube_audio(url: str) -> str:

    output_path = os.path.join(
        DOWNLOAD_DIR,
        "%(title)s.%(ext)s"
    )

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        info = ydl.extract_info(url, download=True)

        filename = ydl.prepare_filename(info)

        filename = os.path.splitext(filename)[0] + ".mp3"

    return filename


# STEP 2: Convert MP3 / local audio into WAV
def convert_to_wav(input_path: str) -> str:

    output_path = os.path.splitext(input_path)[0] + "_converted.wav"

    audio = AudioSegment.from_file(input_path)

    # Convert to mono and 16 kHz
    audio = audio.set_channels(1).set_frame_rate(16000)

    audio.export(output_path, format="wav")

    return output_path


# STEP 3: Split WAV into chunks
def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list:

    audio = AudioSegment.from_wav(wav_path)

    chunk_ms = chunk_minutes * 60 * 1000

    chunks = []

    # Create a separate folder for each input
    filename = os.path.splitext(os.path.basename(wav_path))[0]

    chunk_dir = os.path.join(DOWNLOAD_DIR, filename + "_chunks")

    os.makedirs(chunk_dir, exist_ok=True)

    for i, start in enumerate(range(0, len(audio), chunk_ms)):

        # Extract audio segment
        chunk = audio[start:start + chunk_ms]

        # Generate chunk file path
        chunk_path = os.path.join(
            chunk_dir,
            f"chunk_{i + 1}.wav"
        )

        # Save actual audio data
        chunk.export(chunk_path, format="wav")

        # Store file path
        chunks.append(chunk_path)

    return chunks


# STEP 4: Main processing function
def process_input(source: str) -> list:

    if source.startswith("http://") or source.startswith("https://"):

        print("Detected YouTube URL: Downloading audio...")

        mp3_path = download_youtube_audio(source)

        print("Converting MP3 to WAV...")

        wav_path = convert_to_wav(mp3_path)

    else:

        print("Detected local audio: Converting into WAV...")

        if not os.path.isfile(source):
            raise FileNotFoundError(f"Audio file not found: {source}")

        wav_path = convert_to_wav(source)

    print("Chunking audio...")

    chunks = chunk_audio(wav_path, chunk_minutes=10)

    print(f"Audio ready - {len(chunks)} chunk(s) created.")

    return chunks



