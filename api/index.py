from fastapi import FastAPI, Query
import os
import requests
from datetime import datetime, timedelta, timezone

app = FastAPI()

YT_API_KEY = os.getenv("YT_API_KEY")

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/yt/channel_recent")
def channel_recent(
    channel_id: str = Query(..., description="YouTube channelId, e.g. UC_x5XG1OV2P6uZZ5FSM9Ttw"),
    days: int = Query(30, ge=1, le=365),
    max_results: int = Query(25, ge=1, le=50),
):
    if not YT_API_KEY:
        return {"error": "Missing YT_API_KEY env var"}

    published_after = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat().replace("+00:00", "Z")

    search_url = "https://www.googleapis.com/youtube/v3/search"
    search_params = {
        "key": YT_API_KEY,
        "part": "snippet",
        "channelId": channel_id,
        "publishedAfter": published_after,
        "maxResults": max_results,
        "order": "date",
        "type": "video",
    }
    s = requests.get(search_url, params=search_params, timeout=30)
    s.raise_for_status()
    items = s.json().get("items", [])

    video_ids = [it["id"]["videoId"] for it in items if it.get("id", {}).get("videoId")]
    if not video_ids:
        return {"channel_id": channel_id, "days": days, "videos": []}

    videos_url = "https://www.googleapis.com/youtube/v3/videos"
    videos_params = {
        "key": YT_API_KEY,
        "part": "snippet,statistics,contentDetails",
        "id": ",".join(video_ids),
        "maxResults": max_results,
    }
    v = requests.get(videos_url, params=videos_params, timeout=30)
    v.raise_for_status()
    vitems = v.json().get("items", [])

    videos = []
    for it in vitems:
        videos.append({
            "video_id": it["id"],
            "url": f"https://www.youtube.com/watch?v={it['id']}",
            "title": it["snippet"].get("title"),
            "published_at": it["snippet"].get("publishedAt"),
            "description": it["snippet"].get("description"),
            "thumbnails": it["snippet"].get("thumbnails"),
            "stats": it.get("statistics", {}),
            "duration": it.get("contentDetails", {}).get("duration"),
        })

    return {"channel_id": channel_id, "days": days, "videos": videos}
