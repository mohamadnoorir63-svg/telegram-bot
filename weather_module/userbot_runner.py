from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os, threading, asyncio, yt_dlp, re

# ================== ⚙️ تنظیمات محیطی ==================
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION = os.getenv("SESSION_STRING", "")

# ================== 🤖 ساخت کلاینت Pyrogram (یوزربات) ==================
userbot = Client(
    "userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION
)

# مسیر ذخیره آهنگ‌ها
DOWNLOAD_PATH = "downloads"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

# ================== 🎵 تابع دانلود آهنگ ==================
def download_precise(query: str):
    """دانلود آهنگ از YouTube / YouTube Music / SoundCloud"""
    os.makedirs(DOWNLOAD_PATH, exist_ok=True)
    common_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "outtmpl": f"{DOWNLOAD_PATH}/%(title)s.%(ext)s",
        "retries": 3,
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

    cookiefile = "cookies.txt"
    if os.path.exists(cookiefile):
        common_opts["cookiefile"] = cookiefile

    if re.match(r"^https?://", query.strip(), re.I):
        try:
            with yt_dlp.YoutubeDL(common_opts) as ydl:
                info = ydl.extract_info(query, download=True)
                if "entries" in info:
                    info = info["entries"][0]
                title = info.get("title", "audio")
                mp3_path = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"
                if os.path.exists(mp3_path):
                    return mp3_path, title, "Direct"
        except Exception as e:
            print(f"[Direct ERROR] {e}")

    sources = [
        ("YouTube", f"ytsearch5:{query}"),
        ("YouTube Music", f"ytmusicsearch5:{query}"),
        ("SoundCloud", f"scsearch5:{query}"),
    ]

    for source_name, expr in sources:
        print(f"🔎 جستجو در {source_name} برای {query}")
        try:
            with yt_dlp.YoutubeDL(common_opts) as ydl:
                info = ydl.extract_info(expr, download=True)
                if not info:
                    continue
                if "entries" in info and info["entries"]:
                    info = info["entries"][0]
                title = info.get("title", "audio")
                mp3_path = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"
                if os.path.exists(mp3_path):
                    return mp3_path, title, source_name
        except Exception as e:
            print(f"[{source_name} ERROR] {e}")
            continue
    return None, None, None

# ================== 💬 هندل پیام‌ها ==================
@userbot.on_message(filters.text & (filters.private | filters.group | filters.me))
async def handle_music(client, message):
    text = (message.text or "").strip()

    if text.lower() == "ping":
        return await message.reply_text("✅ Userbot فعال است!")

    if not text.startswith("آهنگ "):
        return

    query = text[len("آهنگ "):].strip()
    if not query:
        return await message.reply_text("❗ لطفاً بعد از 'آهنگ' نام آهنگ را بنویس.")

    m = await message.reply_text(f"🎧 در حال جستجو برای آهنگ: {query} ...")
    try:
        file_path, title, source = await asyncio.to_thread(download_precise, query)
        if not file_path:
            await m.edit("❌ هیچ نتیجه‌ای پیدا نشد یا دانلود ناموفق بود 😔")
            return

        await message.reply_audio(
            audio=file_path,
            caption=f"🎶 {title}\n🌐 منبع: {source}",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🎵 منبع", callback_data="ok")]]
            ),
        )
        await m.delete()
        try:
            os.remove(file_path)
        except:
            pass
    except Exception as e:
        await m.edit(f"❌ خطا:\n`{e}`")
        print(f"[ERROR] {e}")

# ================== 🚀 اجرای Userbot ==================
async def run_userbot():
    """اجرای کامل Userbot"""
    try:
        print("🚀 Starting userbot...")
        await userbot.start()
        me = await userbot.get_me()
        print(f"✅ Userbot وارد شد: {me.first_name} ({me.id})")

        # نگه داشتن ربات (جایگزین idle())
        stop_event = asyncio.Event()
        await stop_event.wait()

    except Exception as e:
        print(f"⚠️ خطا در اجرای userbot: {e}")

def start_userbot():
    """اجرای Userbot در Thread جداگانه"""
    def _worker():
        asyncio.run(run_userbot())

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    print("🌀 Userbot thread started...")
