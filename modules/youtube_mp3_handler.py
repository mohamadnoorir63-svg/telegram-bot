import re
import os
import yt_dlp
import asyncio
from telegram import Update
from telegram.ext import ContextTypes

# ================================
# سودو
# ================================
SUDO_USERS = [8588347189]

# ================================
# مسیر کوکی یوتیوب
# ================================
COOKIE_FILE = "modules/youtube_cookie.txt2"

# ================================
# مسیر دانلود
# ================================
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# ================================
# regex برای لینک (در صورت نیاز)
# ================================
URL_RE = re.compile(r"(https?://[^\s]+)")

# ================================
# تابع دانلود مستقیم MP3 با کوکی
# ================================
def download_audio_stream(query):
    ydl_opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "cookiefile": COOKIE_FILE,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title).200s.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    # اگر متن لینک یوتیوب باشه، مستقیم دانلود کن، وگرنه ytsearch
    url_or_search = query if URL_RE.match(query) else f"ytsearch1:{query}"  # فقط اولین نتیجه
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url_or_search, download=True)
        # نام فایل امن با جایگزینی کاراکترهای غیرمجاز
        title = info.get('title', 'audio')
        safe_title = re.sub(r'[\\/*?:"<>|]', "_", title)
        mp3_file = os.path.join(DOWNLOAD_FOLDER, f"{safe_title}.mp3")
    return mp3_file, info

# ================================
# هندلر تلگرام
# ================================
async def youtube_mp3_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    msg = await update.message.reply_text("🎵 در حال آماده‌سازی MP3 ...")

    loop = asyncio.get_running_loop()
    try:
        mp3_file, info = await loop.run_in_executor(None, download_audio_stream, text)

        if not os.path.exists(mp3_file):
            await msg.edit_text("❌ فایل دانلود نشد یا نام فایل معتبر نیست.")
            return

        await update.message.reply_audio(
            audio=open(mp3_file, "rb"),
            caption=f"🎵 {info.get('title', 'Audio')}"
        )
        os.remove(mp3_file)
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود یا ارسال MP3.\n{e}")
