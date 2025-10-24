import yt_dlp
import random

async def search_music(query, limit=3):
    """
    جستجوی آهنگ در YouTube
    برمی‌گردونه: لیستی از چند نتیجه با عنوان، لینک و مدت زمان
    """
    try:
        ydl_opts = {
            "quiet": True,
            "format": "bestaudio/best",
            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)["entries"]

        songs = []
        for r in results:
            songs.append({
                "title": r.get("title", "Unknown"),
                "url": r.get("webpage_url", ""),
                "duration": r.get("duration", 0),
            })

        return songs

    except Exception as e:
        print(f"⚠️ Search error: {e}")
        return []
