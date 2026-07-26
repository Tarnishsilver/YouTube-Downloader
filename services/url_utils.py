import re
import httpx
from urllib.parse import urlparse, parse_qs


YOUTUBE_HOSTS = ("www.youtube.com", "youtube.com", "m.youtube.com")


def normalize_youtube_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.path.startswith("/shorts/"):
        video_id = parsed.path.split("/")[2]
        return f"https://www.youtube.com/watch?v={video_id}"
    return url


def get_video_id(url: str) -> str:
    parsed = urlparse(url)
    hostname = parsed.hostname.lower() if parsed.hostname else ""

    if hostname == "youtu.be":
        return parsed.path.strip("/")

    if hostname in YOUTUBE_HOSTS:
        if parsed.path.startswith("/shorts/"):
            return parsed.path.split("/")[2]
        query = parse_qs(parsed.query)
        if "v" in query:
            return query["v"][0]

    raise ValueError("Invalid YouTube URL")


def sanitize_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "", name).strip()


def get_video_info(url: str) -> dict:
    response = httpx.get(
        "https://www.youtube.com/oembed",
        params={"url": url, "format": "json"},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    return {
        "title": data["title"],
        "thumbnail_url": data["thumbnail_url"],
        "author_name": data.get("author_name", ""),
    }


def get_video_title(url: str) -> str:
    return get_video_info(url)["title"]


def get_video_thumbnail_url(url: str) -> str:
    return get_video_info(url)["thumbnail_url"]


def get_direct_video_url(url: str) -> str:
    import yt_dlp
    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info["url"]
