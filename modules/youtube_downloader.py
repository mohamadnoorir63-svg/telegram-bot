# modules/youtube_downloader.py
import os
import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes
import re

# مسیر فایل کوکی
COOKIE_FILE = "modules/youtube_cookie.txt"

# اگر فایل کوکی وجود نداشت، بساز
os.makedirs("modules", exist_ok=True)
if not os.path.exists(COOKIE_FILE):
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        f.write("# Paste YouTube cookies here in Netscape format\n")

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

URL_RE = re.compile(r"(https?://[^\s]+)")


async def youtube_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    match = URL_RE.search(text)
    if not match:
        return

    url = match.group(1)

    if "youtube.com" not in url and "youtu.be" not in url:
        return

    msg = await update.message.reply_text("📥 در حال پردازش لینک یوتیوب...")

    ydl_opts = {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "format": "best",
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
        "noplaylist": True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        title = info.get("title", "YouTube Video")

        await msg.edit_text("⬇ در حال ارسال ویدیو...")
        await update.message.reply_video(
            video=open(filename, "rb"),
            caption=f"📥 {title}"
        )

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود یوتیوب:\n{e}")
