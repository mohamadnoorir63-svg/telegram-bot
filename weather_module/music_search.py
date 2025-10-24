import yt_dlp
import random

async def search_music(query):
    try:
        ydl_opts = {"quiet": True, "format": "bestaudio/best"}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)["entries"][0]
            return {
                "title": info["title"],
                "url": info["webpage_url"],
                "duration": info.get("duration", 0)
            }
    except Exception as e:
        print("Search error:", e)
        return None
