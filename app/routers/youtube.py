import uuid
import asyncio
import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, StreamingResponse
from pydantic import BaseModel

from app.task_manager import task_store, process_video
from services.url_utils import get_video_id

router = APIRouter(prefix="/api", tags=["youtube"])


class DownloadRequest(BaseModel):
    url: str


@router.post("/download")
async def start_download(req: DownloadRequest):
    url = req.url.strip()

    try:
        get_video_id(url)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    task_id = str(uuid.uuid4())[:8]
    asyncio.create_task(process_video(url, task_id))

    return {"task_id": task_id, "status": "processing"}


@router.get("/download/{task_id}/status")
async def get_status(task_id: str):
    task = task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    resp = {
        "status": task["status"],
        "progress": task.get("progress", 0),
        "step": task.get("step", ""),
        "title": task.get("title", ""),
        "thumbnail": task.get("thumbnail", ""),
        "author": task.get("author", ""),
    }

    if task["status"] == "completed":
        resp["video_available"] = task["direct_url"] is not None
        resp["captions_available"] = task["captions"] is not None

    if task["status"] == "failed":
        resp["error"] = task.get("error", "Unknown error")

    return resp


@router.get("/download/{task_id}/video")
async def get_video(task_id: str):
    task = task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task["status"] != "completed" or not task.get("direct_url"):
        raise HTTPException(status_code=404, detail="Video not ready yet")

    safe_title = task["title"].encode("ascii", "replace").decode("ascii").replace("?", "_").strip(" _")
    if not safe_title:
        safe_title = "video"

    async def stream():
        async with httpx.AsyncClient(follow_redirects=True) as client:
            async with client.stream("GET", task["direct_url"]) as resp:
                async for chunk in resp.aiter_bytes():
                    yield chunk

    return StreamingResponse(
        stream(),
        media_type="video/mp4",
        headers={"Content-Disposition": f'attachment; filename="{safe_title}.mp4"'},
    )


@router.get("/download/{task_id}/captions/{fmt}")
async def get_captions(task_id: str, fmt: str):
    if fmt not in ("txt", "srt", "vtt"):
        raise HTTPException(status_code=400, detail="Format must be txt, srt, or vtt")

    task = task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task["status"] != "completed" or not task.get("captions"):
        raise HTTPException(status_code=404, detail="Captions not ready yet")

    content = task["captions"][fmt]
    media_types = {"txt": "text/plain", "srt": "text/plain", "vtt": "text/vtt"}
    exts = {"txt": "txt", "srt": "srt", "vtt": "vtt"}

    safe_title = task["title"].encode("ascii", "replace").decode("ascii").replace("?", "_").strip(" _")
    if not safe_title:
        safe_title = "captions"

    return PlainTextResponse(
        content=content,
        media_type=media_types[fmt],
        headers={"Content-Disposition": f'attachment; filename="{safe_title}.{exts[fmt]}"'},
    )
