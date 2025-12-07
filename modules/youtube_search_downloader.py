# modules/youtube_downloader.py
import os
import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes
import re

COOKIE_FILE = "modules/youtube_cookie.txt"

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

URL_RE = re.compile(r"(https?://[^\s]+)")


async def youtube_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    m = URL_RE.search(text)
    if not m:
        return

    url = m.group(1)

    if "youtube.com" not in url and "youtu.be" not in url:
        return

    msg = await update.message.reply_text("🎧 در حال دانلود نسخه صوتی...")

    ydl_opts = {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "format": "bestaudio/best",       # ← فقط بهترین صوت
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = f"{DOWNLOAD_FOLDER}/{info['id']}.mp3"

        title = info.get("title", "Audio File")

        await msg.edit_text("⬇ ارسال فایل صوتی...")

        await update.message.reply_audio(
            audio=open(filename, "rb"),
            caption=f"🎵 {title}"
        )

        os.remove(filename)

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود:\n{e}")
