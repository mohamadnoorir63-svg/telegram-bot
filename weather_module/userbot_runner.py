from pyrogram import Client, filters
import os, threading, asyncio, yt_dlp, re

# ================== ⚙️ تنظیمات محیطی ==================
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION = os.getenv("SESSION_STRING", "")

# ================== 🤖 ساخت کلاینت Pyrogram ==================
        



# 🎵 دانلود آهنگ با دقت بالا (YouTube → YouTube Music → SoundCloud)
def download_precise(query: str):
    os.makedirs("downloads", exist_ok=True)
    common_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "outtmpl": "downloads/%(title)s.%(ext)s",
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
        "extractor_args": {
            "youtube": {"player_client": ["android"]}
        },
    }

    cookiefile = "cookies.txt"
    if os.path.exists(cookiefile):
        common_opts["cookiefile"] = cookiefile

    # ترتیب اولویت منبع‌ها
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


# 💬 پاسخ به پیام‌ها
@app.on_message(filters.text)
async def handle_music(client, message):
    text = message.text.strip()

    # فقط اگر پیام با "آهنگ " شروع شود
    if not text.startswith("آهنگ "):
        return

    query = text[len("آهنگ "):].strip()
    if not query:
        return await message.reply("❗ لطفاً بعد از 'آهنگ' نام آهنگ را بنویس.")

    m = await message.reply("🎧 در حال جستجو برای آهنگ شما، لطفاً صبر کنید...")

    try:
        file_path, title, source = await asyncio.to_thread(download_precise, query)
        if not file_path:
            raise Exception("هیچ آهنگی برای این نام پیدا نشد 😔")

        await message.reply_audio(
            audio=file_path,
            caption=f"🎶 آهنگ شما:\n**{title}**\n🌐 منبع: {source}",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🎵 منبع", callback_data="ok")]]
            )
        )

        await m.delete()
        os.remove(file_path)

    except Exception as e:
        await m.edit(f"❌ خطا:\n`{e}`")
        print(f"[ERROR] {e}")
    
# ================== 🚀 اجرای Userbot ==================
async def run_userbot():
    """اجرای کامل یوزربات"""
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
