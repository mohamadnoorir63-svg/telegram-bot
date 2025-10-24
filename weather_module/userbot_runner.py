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

# ================== 🎵 دانلود از چند منبع با انتخاب بهینه ==================
def download_precise(query: str):
    """
    دانلود آهنگ با اولویت: YouTube → YouTube Music → SoundCloud
    - اگر ورودی لینک باشد مستقیم دانلود می‌کند.
    """
    os.makedirs(DOWNLOAD_PATH, exist_ok=True)

    common_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "outtmpl": f"{DOWNLOAD_PATH}/%(title)s.%(ext)s",
        "ignoreerrors": True,
        "retries": 3,
        "fragment_retries": 3,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "concurrent_fragment_downloads": 3,
        "socket_timeout": 10,
        "extractor_args": {
            "youtube": {"player_client": ["android"]}  # برای دور زدن برخی محدودیت‌ها
        },
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    cookiefile = "cookies.txt"
    if os.path.exists(cookiefile):
        common_opts["cookiefile"] = cookiefile

    # اگر لینک مستقیم بود
    if re.match(r"^https?://", query.strip(), re.I):
        try:
            with yt_dlp.YoutubeDL(common_opts) as ydl:
                info = ydl.extract_info(query, download=True)
                if "entries" in info:
                    info = info["entries"][0]
                title = info.get("title", "audio")
                mp3_path = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"
                if os.path.exists(mp3_path):
                    return mp3_path, title, "Direct URL"
        except Exception as e:
            print(f"[Direct URL ERROR] {e}")

    # جستجو در منابع
    sources = [
        ("YouTube",       f"ytsearch10:{query} audio"),
        ("YouTube Music", f"ytmusicsearch10:{query}"),
        ("SoundCloud",    f"scsearch5:{query}"),
    ]

    for source_name, expr in sources:
        try:
            with yt_dlp.YoutubeDL({**common_opts, "download": True}) as ydl:
                info = ydl.extract_info(expr, download=True)
                if not info:
                    continue

                # اگر لیست بود، اولین نتیجه‌ی معتبر را بردار
                if "entries" in info and info["entries"]:
                    # ترجیحاً آیتم با مدت زیر 12 دقیقه
                    entry = None
                    for e in info["entries"]:
                        if e:
                            dur = (e.get("duration") or 0)
                            if dur == 0 or dur <= 12 * 60:
                                entry = e
                                break
                    if not entry:
                        entry = next((e for e in info["entries"] if e), None)
                    info = entry or info["entries"][0]

                title = info.get("title", "audio")
                mp3_path = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"

                if os.path.exists(mp3_path):
                    return mp3_path, title, source_name
        except Exception as e:
            print(f"[{source_name} ERROR] {e}")
            continue

    return None, None, None

# ================== 💬 هندل پیام‌ها (Pyrogram) ==================
@userbot.on_message(filters.text & (filters.private | filters.group | filters.me))
async def handle_music(client, message):
    text = (message.text or "").strip()

    # فقط اگر پیام با "آهنگ " شروع شود
    if not text.startswith("آهنگ "):
        # پینگ ساده
        if text.lower() == "ping":
            return await message.reply_text("✅ Userbot فعال است!")
        return

    query = text[len("آهنگ "):].strip()
    if not query:
        return await message.reply_text("❗ لطفاً بعد از 'آهنگ' نام آهنگ را بنویس.")

    m = await message.reply_text("🎧 در حال جستجو برای آهنگ شما، لطفاً صبر کنید...")

    try:
        # اجرای دانلود در ترد جدا تا event loop فریز نشود
        file_path, title, source = await asyncio.to_thread(download_precise, query)

        if not file_path:
            await m.edit_text("❌ هیچ نتیجه‌ای پیدا نشد یا دانلود ناموفق بود 😔")
            return

        await message.reply_audio(
            audio=file_path,
            caption=f"🎶 آهنگ شما:\n<b>{title}</b>\n🌐 منبع: <i>{source}</i>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🎵 باشه", callback_data="ok")]]
            )
        )
        await m.delete()

        # پاکسازی فایل
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"[CLEANUP ERROR] {e}")

    except Exception as e:
        await m.edit_text(f"❌ خطا:\n`{e}`", parse_mode="Markdown")
        print(f"[ERROR] {e}")

# ================== 🚀 اجرای userbot (برای وقتی این فایل مستقل اجرا شود) ==================
async def run_userbot():
    try:
        print("🚀 Starting userbot...")
        await userbot.start()
        me = await userbot.get_me()
        print(f"✅ Userbot وارد شد: {me.first_name} ({me.id})")
        await userbot.idle()
    except Exception as e:
        print(f"⚠️ خطا در اجرای userbot: {e}")

def start_userbot():
    """اگر این ماژول را از bot اصلی ایمپورت می‌کنی، این فانکشن را صدا بزن تا در Thread جدا اجرا شود."""
    def _worker():
        asyncio.run(run_userbot())

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    print("🌀 Userbot thread started...")
