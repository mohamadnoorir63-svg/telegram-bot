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


# ================== 🎧 تابع دانلود آهنگ ==================
def download_song(query: str):
    """دانلود آهنگ از YouTube"""
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "outtmpl": f"{DOWNLOAD_PATH}/%(title)s.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=True)
            if "entries" in info:
                info = info["entries"][0]

            title = info.get("title", "music")
            filename = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"
            print(f"✅ دانلود شد: {title}")
            return filename, title
    except Exception as e:
        print(f"⚠️ خطا در دانلود آهنگ: {e}")
        return None, None


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

        m = await message.reply_text(f"🎧 در حال جستجو و دانلود آهنگ: {query} ...")

        # اجرای دانلود در thread جدا تا ربات هنگ نکنه
        loop = asyncio.get_running_loop()
        file_path, title = await loop.run_in_executor(None, download_song, query)

        if not file_path or not os.path.exists(file_path):
            return await m.edit("❌ خطا در دانلود آهنگ 😔")

        await message.reply_audio(
            audio=file_path,
            caption=f"🎶 {title}",
        )
        await m.delete()

        # حذف فایل پس از ارسال
        try:
            os.remove(file_path)
        except:
            pass


# ================== ⚡ اتصال بین Userbot و Bot Token ==================
async def send_song_request_from_bot(query, chat_id):
    """
    این تابع از سمت Bot Token فراخوانی می‌شود و دستور آهنگ را به یوزربات می‌فرستد.
    """
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
