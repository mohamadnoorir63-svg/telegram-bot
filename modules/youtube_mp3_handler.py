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
# regex برای لینک
# ================================
URL_RE = re.compile(r"(https?://[^\s]+)")

# ================================
# تابع دانلود مستقیم MP3 با کوکی
# ================================
def download_audio_stream(url_or_search):
    ydl_opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "cookiefile": COOKIE_FILE,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url_or_search, download=True)
        filename = ydl.prepare_filename(info)
    return filename, info

# ================================
# هندلر تلگرام
# ================================
async def youtube_mp3_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    msg = await update.message.reply_text("🎵 در حال آماده‌سازی موسیقی ...")

    loop = asyncio.get_running_loop()
    try:
        # اگر لینک باشه مستقیم استفاده می‌کنیم، در غیر اینصورت جستجو
        url_or_search = text if URL_RE.match(text) else f"ytsearch:{text}"

        file_path, info = await loop.run_in_executor(None, download_audio_stream, url_or_search)

        # ارسال فایل صوتی
        await update.message.reply_audio(audio=open(file_path, "rb"),
                                         caption=f"🎵 {info.get('title', 'Audio')}")
        os.remove(file_path)
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود یا ارسال موسیقی.\n{e}")
