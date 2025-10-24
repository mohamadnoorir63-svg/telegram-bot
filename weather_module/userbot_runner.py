from pyrogram import Client, filters
import os, threading, asyncio, yt_dlp, re

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

# ================== 🎵 تابع دانلود چندمنبعی ==================
def download_precise(query: str):
    """
    جستجو و دانلود آهنگ از YouTube → YouTube Music → SoundCloud
    """
    os.makedirs(DOWNLOAD_PATH, exist_ok=True)

    base_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "outtmpl": f"{DOWNLOAD_PATH}/%(title)s.%(ext)s",
        "retries": 3,
        "fragment_retries": 3,
        "ignoreerrors": True,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "concurrent_fragment_downloads": 3,
        "socket_timeout": 10,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    cookiefile = "cookies.txt"
    if os.path.exists(cookiefile):
        base_opts["cookiefile"] = cookiefile

    # 📌 اگر لینک مستقیم بود
    if re.match(r"^https?://", query.strip(), re.I):
        try:
            with yt_dlp.YoutubeDL(base_opts) as ydl:
                info = ydl.extract_info(query, download=True)
                if "entries" in info:
                    info = info["entries"][0]
                title = info.get("title", "audio")
                mp3_path = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"
                if os.path.exists(mp3_path):
                    print(f"[✅ Direct URL] {title}")
                    return mp3_path, title, "Direct URL"
        except Exception as e:
            print(f"[❌ Direct ERROR] {e}")

    # منابع جستجو
    sources = [
        ("YouTube", f"ytsearch10:{query} audio"),
        ("YouTube Music", f"ytmusicsearch10:{query}"),
        ("SoundCloud", f"scsearch5:{query}"),
    ]

    for source_name, expr in sources:
        print(f"🔎 جستجو در {source_name} → {expr}")
        try:
            with yt_dlp.YoutubeDL({**base_opts, "download": True}) as ydl:
                info = ydl.extract_info(expr, download=True)
                if "entries" in info and info["entries"]:
                    info = info["entries"][0]

                if not info:
                    print(f"⚠️ {source_name}: نتیجه‌ای نداشت")
                    continue

                title = info.get("title", "audio")
                mp3_path = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"
                if os.path.exists(mp3_path):
                    print(f"[✅ Downloaded] {title} ← {source_name}")
                    return mp3_path, title, source_name
                else:
                    print(f"⚠️ {source_name}: فایل mp3 ساخته نشد")

        except Exception as e:
            print(f"[❌ {source_name} ERROR] {e}")

    print("🚫 هیچ منبعی جواب نداد")
    return None, None, None


# ================== 💬 هندل پیام‌ها ==================
@userbot.on_message(filters.text & (filters.private | filters.group | filters.me))
async def handle_message(client, message):
    text = (message.text or "").strip()
    print(f"📩 [Userbot] پیام دریافت شد: {text}")

    # 🔹 تست اتصال
    if text.lower() == "ping":
        return await message.reply_text("✅ Userbot فعال است!")

    # 🔹 درخواست آهنگ
    if not text.startswith("آهنگ "):
        return

    query = text.replace("آهنگ", "").strip()
    if not query:
        return await message.reply_text("❗ لطفاً بعد از 'آهنگ' نام آهنگ را بنویس.")

    m = await message.reply_text(f"🎧 در حال جستجو برای آهنگ: {query} ...")

    # دانلود در thread جدا (برای جلوگیری از فریز شدن event loop)
    loop = asyncio.get_running_loop()
    file_path, title, source = await loop.run_in_executor(None, download_precise, query)

    if not file_path or not os.path.exists(file_path):
        return await m.edit("❌ هیچ نتیجه‌ای پیدا نشد یا دانلود ناموفق بود 😔")

    await message.reply_audio(
        audio=file_path,
        caption=f"🎶 {title}\n🌐 منبع: {source}",
    )
    await m.delete()

    # حذف فایل پس از ارسال
    try:
        os.remove(file_path)
    except:
        pass


# ================== 🚀 اجرای Userbot ==================
async def run_userbot():
    """اجرای کامل یوزربات (با Pyrogram جدید، بدون idle)"""
    try:
        print("🚀 Starting userbot...")
        await userbot.start()
        me = await userbot.get_me()
        print(f"✅ Userbot وارد شد: {me.first_name} ({me.id})")

        # نگه داشتن ربات بدون idle()
        stop_event = asyncio.Event()
        await stop_event.wait()

    except Exception as e:
        print(f"⚠️ خطا در اجرای userbot: {e}")


def start_userbot():
    """اجرای Userbot در Thread جداگانه برای هماهنگی با خنگول"""
    def _worker():
        # ✅ ساخت لوپ جدید مخصوص ترد
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_userbot())

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    print("🌀 Userbot thread started...")
