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

# ================== 🎵 دانلود از چند منبع (YouTube / YT Music / SoundCloud) ==================
def download_precise(query: str):
    """دانلود آهنگ با جستجو در چند منبع"""
    os.makedirs(DOWNLOAD_PATH, exist_ok=True)
    common_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "outtmpl": f"{DOWNLOAD_PATH}/%(title)s.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "ignoreerrors": True,
        "retries": 3,
        "fragment_retries": 3,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "concurrent_fragment_downloads": 3,
        "extractor_args": {"youtube": {"player_client": ["android"]}},
    }

    cookiefile = "cookies.txt"
    if os.path.exists(cookiefile):
        common_opts["cookiefile"] = cookiefile

    sources = [
        ("YouTube", f"ytsearch1:{query}"),
        ("YouTube Music", f"ytmusicsearch1:{query}"),
        ("SoundCloud", f"scsearch1:{query}"),
    ]

    for source_name, expr in sources:
        try:
            with yt_dlp.YoutubeDL(common_opts) as ydl:
                info = ydl.extract_info(expr, download=True)
                if not info:
                    continue

                entry = None
                if "entries" in info and info["entries"]:
                    for e in info["entries"]:
                        if e:
                            entry = e
                            break
                else:
                    entry = info

                if not entry:
                    continue

                title = entry.get("title", "audio")
                with yt_dlp.YoutubeDL({**common_opts, "download": False}) as y2:
                    prepared = y2.prepare_filename(entry)
                mp3_path = os.path.splitext(prepared)[0] + ".mp3"

                if os.path.exists(mp3_path):
                    print(f"[✅ Found] {title} from {source_name}")
                    return mp3_path, title, source_name

        except Exception as e:
            print(f"[{source_name} ERROR] {e}")
            continue

    return None, None, None


# ================== 💬 هندلر پیام‌های دریافتی ==================
@userbot.on_message(filters.text & (filters.private | filters.group | filters.me))
async def handle_message(client, message):
    text = message.text.strip()
    print(f"📩 [Userbot] پیام: {text}")

    # 🔹 تست اتصال
    if text.lower() == "ping":
        return await message.reply_text("✅ Userbot فعال است!")

    # 🔹 درخواست آهنگ
    if text.startswith("آهنگ "):
        query = text.replace("آهنگ", "").strip()
        if not query:
            return await message.reply_text("❗ لطفاً بعد از 'آهنگ' نام آهنگ را بنویس.")

        m = await message.reply_text(f"🎧 در حال جستجو برای آهنگ: {query} ...")

        loop = asyncio.get_running_loop()
        file_path, title, source = await loop.run_in_executor(None, download_precise, query)

        if not file_path or not os.path.exists(file_path):
            return await m.edit("❌ هیچ آهنگی با این نام پیدا نشد 😔")

        await message.reply_audio(
            audio=file_path,
            caption=f"🎶 {title}\n🌐 منبع: {source}",
        )
        await m.delete()

        try:
            os.remove(file_path)
        except:
            pass


# ================== ⚡ اتصال بین Userbot و Bot Token ==================
async def send_song_request_from_bot(query, chat_id):
    """ارسال درخواست آهنگ از Bot Token به Userbot"""
    try:
        if not userbot.is_connected:
            print("⚠️ Userbot هنوز بالا نیامده!")
            return False

        await userbot.send_message(chat_id, f"آهنگ {query}")
        print(f"📤 درخواست آهنگ برای Userbot ارسال شد: {query}")
        return True
    except Exception as e:
        print(f"⚠️ خطا در ارسال پیام از Bot به Userbot: {e}")
        return False


# ================== 🚀 اجرای یوزربات ==================
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
    """اجرای Userbot در Thread جداگانه برای جلوگیری از تداخل asyncio"""
    def _worker():
        asyncio.run(run_userbot())

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    print("🌀 Userbot thread started...")
