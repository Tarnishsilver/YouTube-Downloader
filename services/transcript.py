from youtube_transcript_api import YouTubeTranscriptApi

LANGUAGES = ["hi", "en", "mr", "gu", "ta", "te", "kn", "ml", "bn", "pa"]


def _seconds_to_srt(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _seconds_to_vtt(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def fetch_transcript(video_id: str) -> list[dict] | None:
    try:
        transcript = YouTubeTranscriptApi().fetch(video_id, languages=LANGUAGES)
        return [
            {"text": segment.text, "start": segment.start, "duration": segment.duration}
            for segment in transcript
        ]
    except Exception:
        return None


def format_as_txt(segments: list[dict]) -> str:
    return "\n".join(seg["text"] for seg in segments)


def format_as_srt(segments: list[dict]) -> str:
    lines = []
    for i, seg in enumerate(segments, 1):
        start = _seconds_to_srt(seg["start"])
        end = _seconds_to_srt(seg["start"] + seg["duration"])
        lines.append(f"{i}\n{start} --> {end}\n{seg['text']}\n")
    return "\n".join(lines)


def format_as_vtt(segments: list[dict]) -> str:
    lines = ["WEBVTT\n"]
    for seg in segments:
        start = _seconds_to_vtt(seg["start"])
        end = _seconds_to_vtt(seg["start"] + seg["duration"])
        lines.append(f"{start} --> {end}\n{seg['text']}\n")
    return "\n".join(lines)
