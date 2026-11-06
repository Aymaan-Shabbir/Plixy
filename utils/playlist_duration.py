
import yt_dlp


def calculate_playlist_duration(
    playlist_url: str,
    start_video: int = 1,
) -> dict:

    if start_video < 1:
        raise ValueError("Starting video number must be at least 1.")

    options = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": "in_playlist",
        "ignoreerrors": True,
        "skip_download": True,
        "noplaylist": False,
    }

    with yt_dlp.YoutubeDL(options) as ydl:

        playlist = ydl.extract_info(
            playlist_url,
            download=False,
        )

    if not playlist:
        raise ValueError(
            "Unable to extract playlist. Check the URL and accessibility."
        )

    entries = playlist.get("entries") or []

    total_videos = len(entries)

    if total_videos == 0:
        raise ValueError("No videos found in this playlist.")

    if start_video > total_videos:
        raise ValueError(
            f"Starting video number exceeds playlist size ({total_videos})."
        )

    selected_entries = entries[start_video - 1:]

    total_seconds = 0
    processed_videos = 0
    skipped_entries = []

    # Metadata extraction for individual videos.
    video_options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        "ignoreerrors": True,
    }

    with yt_dlp.YoutubeDL(video_options) as video_ydl:

        for index, entry in enumerate(selected_entries, start=start_video):

            if not entry:
                skipped_entries.append({
                    "number": index,
                    "title": "Unavailable video",
                })
                continue

            title = entry.get("title") or f"Video {index}"
            duration = entry.get("duration")

            # Fetch individual metadata if flat extraction
            # did not provide a duration.
            if duration is None:

                video_url = (
                    entry.get("webpage_url")
                    or entry.get("url")
                )

                video_id = entry.get("id")

                if video_url and not video_url.startswith("http"):
                    video_url = (
                        f"https://www.youtube.com/watch?v={video_url}"
                    )

                if not video_url and video_id:
                    video_url = (
                        f"https://www.youtube.com/watch?v={video_id}"
                    )

                if video_url:

                    try:
                        video_info = video_ydl.extract_info(
                            video_url,
                            download=False,
                        )

                        if video_info:
                            duration = video_info.get("duration")
                            title = video_info.get("title") or title

                    except Exception:
                        duration = None

            if duration is None or duration <= 0:

                skipped_entries.append({
                    "number": index,
                    "title": title,
                })

                continue

            total_seconds += int(duration)
            processed_videos += 1

    return {
        "playlist_title": playlist.get("title", "YouTube Playlist"),
        "total_videos": total_videos,
        "start_video": start_video,
        "processed_videos": processed_videos,
        "skipped_videos": len(skipped_entries),
        "skipped_entries": skipped_entries,
        "total_seconds": total_seconds,
    }
