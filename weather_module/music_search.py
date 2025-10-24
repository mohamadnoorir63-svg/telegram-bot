import yt_dlp
import random

async def search_music(query, limit=3):
    """
    جستجوی آهنگ در YouTube و SoundCloud
    برمی‌گردونه: لیستی از چند نتیجه با عنوان، لینک و مدت زمان
    """
    results = []
    sources = [
        ("YouTube", f"ytsearch{limit}:{query}"),
        ("YouTube Music", f"ytmusicsearch{limit}:{query}"),
        ("SoundCloud", f"scsearch{limit}:{query}")
    ]

    for source_name, expr in sources:
        try:
            ydl_opts = {
                "quiet": True,
                "noplaylist": True,
                "extract_flat": True,  # فقط لینک‌ها، بدون دانلود
                "format": "bestaudio/best",
                "geo_bypass": True,
                "ignoreerrors": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(expr, download=False)
                if not info or "entries" not in info:
                    continue

                for r in info["entries"]:
                    if not r:
                        continue
                    results.append({
                        "title": r.get("title", "Unknown"),
                        "url": r.get("url") or r.get("webpage_url", ""),
                        "duration": r.get("duration", 0),
                        "source": source_name,
                    })

            if results:
                print(f"✅ Found {len(results)} results from {source_name}")
                break

        except Exception as e:
            print(f"⚠️ Search error in {source_name}: {e}")
            continue

    return results[:limit]
