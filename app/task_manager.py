import asyncio
from services.url_utils import normalize_youtube_url, get_video_info, get_video_id, get_direct_video_url
from services.transcript import fetch_transcript, format_as_txt, format_as_srt, format_as_vtt

task_store: dict[str, dict] = {}


async def process_video(url: str, task_id: str) -> None:
    task_store[task_id] = {
        "status": "fetching_info",
        "progress": 0,
        "step": "Fetching video info...",
        "title": "",
        "thumbnail": "",
        "author": "",
        "direct_url": None,
        "captions": None,
    }

    try:
        normalized_url = normalize_youtube_url(url)
        info = get_video_info(normalized_url)
        task_store[task_id].update({
            "title": info["title"],
            "thumbnail": info["thumbnail_url"],
            "author": info["author_name"],
            "status": "resolving_url",
            "progress": 30,
            "step": "Resolving direct video URL...",
        })

        direct_url = get_direct_video_url(normalized_url)
        task_store[task_id].update({
            "direct_url": direct_url,
            "status": "fetching_transcript",
            "progress": 60,
            "step": "Fetching captions...",
        })

        video_id = get_video_id(normalized_url)
        segments = await asyncio.to_thread(fetch_transcript, video_id)

        if segments:
            task_store[task_id]["captions"] = {
                "txt": format_as_txt(segments),
                "srt": format_as_srt(segments),
                "vtt": format_as_vtt(segments),
            }

        task_store[task_id].update({
            "status": "completed",
            "progress": 100,
            "step": "Complete!",
        })

    except Exception as e:
        task_store[task_id]["status"] = "failed"
        task_store[task_id]["error"] = str(e)
