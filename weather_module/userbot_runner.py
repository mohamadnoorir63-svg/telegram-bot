from pyrogram import Client, filters
import os, threading, asyncio, yt_dlp, re

# ⚙️ تنظیمات محیطی
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION = os.getenv("SESSION_STRING", "")

userbot = Client(
    "userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION
)

def download_precise(query: str):
    """
    جستجو و دانلود آهنگ از سایت‌های ایرانی (Aparat, Namasha, Tamasha)
    """
    base_opts = {
        "format": "bestaudio/best",
        "quiet": False,
        "noplaylist": True,
        "outtmpl": f"{DOWNLOAD_PATH}/%(title)s.%(ext)s",
        "retries": 3,
        "ignoreerrors": True,
        "geo_bypass": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    sources = [
        ("Aparat", f"https://www.aparat.com/result/{query}"),
        ("Namasha", f"https://www.namasha.com/search?query={query}"),
        ("Tamasha", f"https://www.tamasha.com/search?query={query}")
    ]

    for source_name, expr in sources:
        print(f"🔎 جستجو در {source_name} → {expr}")
        try:
            with yt_dlp.YoutubeDL(base_opts) as ydl:
                info = ydl.extract_info(expr, download=True)
                if "entries" in info and info["entries"]:
                    info = info["entries"][0]

                if not info:
                    continue

                title = info.get("title", "audio")
                mp3_path = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"
                if os.path.exists(mp3_path):
                    print(f"[✅ Downloaded] {title} ← {source_name}")
                    return mp3_path, title, source_name

        except Exception as e:
            print(f"[❌ {source_name} ERROR] {e}")

    return None, None, None

# 💬 هندل پیام‌ها
@userbot.on_message(filters.text & (filters.private | filters.me))
async def handle_message(client, message):
    text = (message.text or "").strip()
    print(f"📩 پیام دریافت شد: {text}")

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
            return await m.edit("❌ هیچ نتیجه‌ای پیدا نشد یا دانلود ناموفق بود 😔")

        await message.reply_audio(audio=file_path, caption=f"🎶 {title}\n🌐 منبع: {source}")
        await m.delete()

        try:
            os.remove(file_path)
        except:
            pass


# 🚀 اجرای یوزربوت
async def run_userbot():
    try:
        print("🚀 Starting userbot...")
        await userbot.start()
        me = await userbot.get_me()
        print(f"✅ Logged in as {me.first_name} ({me.id})")

        stop_event = asyncio.Event()
        await stop_event.wait()
    except Exception as e:
        print(f"⚠️ خطا در اجرای userbot: {e}")


def start_userbot():
    def _worker():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_userbot())

    threading.Thread(target=_worker, daemon=True).start()
    print("🌀 Userbot thread started...")
