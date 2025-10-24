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


# ================== 🎵 دانلود از SoundCloud ==================
def download_precise(query: str):
    """
    جستجو و دانلود آهنگ فقط از SoundCloud
    """
    os.makedirs(DOWNLOAD_PATH, exist_ok=True)

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": False,
        "noplaylist": True,
        "outtmpl": f"{DOWNLOAD_PATH}/%(title)s.%(ext)s",
        "retries": 3,
        "fragment_retries": 3,
        "ignoreerrors": True,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "socket_timeout": 10,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    try:
        print(f"🎧 جستجو در SoundCloud → {query}")
        with yt_dlp.YoutubeDL({**ydl_opts, "download": True}) as ydl:
            info = ydl.extract_info(f"scsearch1:{query}", download=True)

            if "entries" in info and info["entries"]:
                info = info["entries"][0]

            if not info:
                print("⚠️ SoundCloud نتیجه‌ای برنگرداند.")
                return None, None, None

            title = info.get("title", "audio")
            mp3_path = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"

            if os.path.exists(mp3_path):
                print(f"[✅ Downloaded] {title} ← SoundCloud")
                return mp3_path, title, "SoundCloud"
            else:
                print("⚠️ فایل mp3 ساخته نشد.")
                return None, None, None

    except Exception as e:
        print(f"[❌ SoundCloud ERROR] {type(e).__name__}: {e}")
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

    m = await message.reply_text(f"🎧 در حال جستجو در SoundCloud برای: {query} ...")

    loop = asyncio.get_running_loop()
    file_path, title, source = await loop.run_in_executor(None, download_precise, query)

    if not file_path or not os.path.exists(file_path):
        return await m.edit("❌ هیچ نتیجه‌ای پیدا نشد یا دانلود ناموفق بود 😔")

    await message.reply_audio(
        audio=file_path,
        caption=f"🎶 {title}\n🌐 منبع: {source}",
    )
    await m.delete()

    try:
        os.remove(file_path)
    except:
        pass


# ================== 🚀 اجرای Userbot ==================
async def run_userbot():
    """اجرای کامل یوزربات (بدون idle)"""
    try:
        print("🚀 Starting userbot...")
        await userbot.start()
        me = await userbot.get_me()
        print(f"✅ Userbot وارد شد: {me.first_name} ({me.id})")

        stop_event = asyncio.Event()
        await stop_event.wait()

    except Exception as e:
        print(f"⚠️ خطا در اجرای userbot: {e}")


def start_userbot():
    """اجرای Userbot در Thread جداگانه برای هماهنگی با خنگول"""
    def _worker():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_userbot())

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    print("🌀 Userbot thread started...")
