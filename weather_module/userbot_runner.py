from pyrogram import Client, filters
import os, threading, asyncio, yt_dlp

# ================== ⚙️ تنظیمات محیطی ==================
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION = os.getenv("SESSION_STRING", "")

# ================== 🤖 ساخت کلاینت Pyrogram ==================
userbot = Client(
    "userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION
)

# مسیر ذخیره آهنگ‌ها
DOWNLOAD_PATH = "downloads"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

# ================== 🎵 دانلود از چند منبع با انتخاب بهینه ==================
def download_precise(query: str):
    """
    - اگر ورودی لینک باشد: همان لینک را دانلود می‌کند.
    - اگر جستجو باشد: از YouTube / YT Music / SoundCloud جستجو می‌کند،
      بهترین نتیجه (< 12min) را گرفته و با URL دقیق دانلود می‌کند.
    """
    import re
    os.makedirs(DOWNLOAD_PATH, exist_ok=True)

    base_opts = {
        "quiet": True,
        "noplaylist": True,
        "outtmpl": f"{DOWNLOAD_PATH}/%(title)s.%(ext)s",
        "retries": 3,
        "fragment_retries": 3,
        "ignoreerrors": True,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "extractor_args": {"youtube": {"player_client": ["android"]}},
        "concurrent_fragment_downloads": 3,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    cookiefile = "cookies.txt"
    if os.path.exists(cookiefile):
        base_opts["cookiefile"] = cookiefile

    # اگر query لینک است، مستقیم دانلود کن
    is_url = re.match(r"^https?://", query.strip(), re.I) is not None
    if is_url:
        try:
            with yt_dlp.YoutubeDL({**base_opts, "format": "bestaudio/best"}) as ydl:
                info = ydl.extract_info(query, download=True)
                if "entries" in info:
                    info = info["entries"][0]
                with yt_dlp.YoutubeDL({**base_opts, "download": False}) as y2:
                    prepared = y2.prepare_filename(info)
                mp3_path = os.path.splitext(prepared)[0] + ".mp3"
                title = info.get("title", "audio")
                if os.path.exists(mp3_path):
                    print(f"[✅ Direct URL] {title}")
                    return mp3_path, title, "Direct"
        except Exception as e:
            print(f"[Direct URL ERROR] {e}")

    # منابع جستجو
    sources = [
        ("YouTube",       f"ytsearch5:{query} audio"),
        ("YouTube Music", f"ytmusicsearch10:{query}"),
        ("SoundCloud",    f"scsearch5:{query}"),
    ]

    def pick_entry(info):
        # از نتایج، اولین آیتم معتبر با مدت < 12 دقیقه را انتخاب کن
        entries = []
        if "entries" in info and info["entries"]:
            entries = [e for e in info["entries"] if e]
        else:
            entries = [info] if info else []
        for e in entries:
            dur = e.get("duration", 0) or 0
            if dur == 0 or dur <= 12 * 60:
                return e
        return entries[0] if entries else None

    for source_name, expr in sources:
        try:
            # مرحله ۱: فقط استخراج اطلاعات (بدون دانلود) تا URL دقیق بگیریم
            with yt_dlp.YoutubeDL({**base_opts, "download": False, "format": "bestaudio/best"}) as ydl_info:
                info = ydl_info.extract_info(expr, download=False)
                if not info:
                    continue
                entry = pick_entry(info)
                if not entry:
                    continue

                url = entry.get("webpage_url") or entry.get("url")
                title = entry.get("title", "audio")
                if not url:
                    continue

            # مرحله ۲: دانلود با URL دقیق
            with yt_dlp.YoutubeDL({**base_opts, "format": "bestaudio/best"}) as ydl_dl:
                info2 = ydl_dl.extract_info(url, download=True)

                if "entries" in info2:
                    info2 = info2["entries"][0]
                with yt_dlp.YoutubeDL({**base_opts, "download": False}) as y2:
                    prepared = y2.prepare_filename(info2)
                mp3_path = os.path.splitext(prepared)[0] + ".mp3"

                if os.path.exists(mp3_path):
                    print(f"[✅ Found] {title} from {source_name}")
                    return mp3_path, title, source_name

        except Exception as e:
            print(f"[{source_name} ERROR] {e}")
            # Fallback: یک دانلود ساده‌تر مستقیماً از عبارت سرچ (گاهی کار می‌کند)
            try:
                with yt_dlp.YoutubeDL({**base_opts, "format": "bestaudio/best"}) as ydl_fallback:
                    info_f = ydl_fallback.extract_info(expr, download=True)
                    if "entries" in info_f:
                        info_f = info_f["entries"][0]
                    with yt_dlp.YoutubeDL({**base_opts, "download": False}) as y2:
                        prepared = y2.prepare_filename(info_f)
                    mp3_path = os.path.splitext(prepared)[0] + ".mp3"
                    title = info_f.get("title", "audio")
                    if os.path.exists(mp3_path):
                        print(f"[✅ Fallback] {title} from {source_name}")
                        return mp3_path, title, source_name
            except Exception as ee:
                print(f"[{source_name} Fallback ERROR] {ee}")
            continue

    return None, None, None


# ================== 💬 هندلر پیام‌های دریافتی ==================
@userbot.on_message(filters.text & (filters.private | filters.group | filters.me))
async def handle_message(client, message):
    text = message.text.strip()
    print(f"📩 [Userbot] پیام: {text}")

    if text.lower() == "ping":
        return await message.reply_text("✅ Userbot فعال است!")

    if text.startswith("آهنگ "):
        query = text.replace("آهنگ", "").strip()
        if not query:
            return await message.reply_text("❗ لطفاً بعد از 'آهنگ' نام آهنگ را بنویس.")

        m = await message.reply_text(f"🎧 در حال جستجو برای آهنگ: {query} ...")

        loop = asyncio.get_running_loop()
        file_path, title, source = await loop.run_in_executor(None, download_precise, query)

        if not file_path or not os.path.exists(file_path):
            return await m.edit("❌ نتیجه‌ای پیدا نشد یا دانلود ناموفق بود. اسم دقیق‌تری بفرست یا یک لینک مستقیم بده 🙏")

        await message.reply_audio(
            audio=file_path,
            caption=f"🎶 {title}\n🌐 منبع: {source}",
        )
        await m.delete()

        try:
            os.remove(file_path)
        except:
            pass
def start_userbot():
    """اجرای Userbot در Thread جداگانه برای جلوگیری از تداخل asyncio"""
    def _worker():
        asyncio.run(run_userbot())

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    print("🌀 Userbot thread started...")
