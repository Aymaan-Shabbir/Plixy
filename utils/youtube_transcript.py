import re
from urllib.parse import parse_qs, urlparse

from youtube_transcript_api import YouTubeTranscriptApi


def fetch_youtube_transcript(url: str, languages: list[str]) -> str:
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower().split(":")[0]
    path_parts = [part for part in parsed.path.split("/") if part]

    video_id = None

    if host in {"youtu.be", "www.youtu.be"} and path_parts:
        video_id = path_parts[0]

    elif host in {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "music.youtube.com",
        "youtube-nocookie.com",
        "www.youtube-nocookie.com",
    }:
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [None])[0]
        elif len(path_parts) >= 2 and path_parts[0] in {
            "shorts",
            "embed",
            "live",
        }:
            video_id = path_parts[1]

    if not video_id or not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise ValueError("Please enter a valid YouTube video URL.")

    fetched = YouTubeTranscriptApi().fetch(
        video_id,
        languages=languages,
    )

    transcript = " ".join(
        snippet.text.strip()
        for snippet in fetched
        if snippet.text.strip()
    )

    if not transcript:
        raise ValueError("No usable captions were found for this video.")

    return transcript