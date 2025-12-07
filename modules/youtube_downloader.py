# modules/youtube_downloader.py
import os
import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes
import re

# مسیر فایل کوکی (باید خودت داخلش کوکی‌ها را قرار بدهی)
COOKIE_FILE = "modules/youtube_cookie.txt"

# ساخت فایل کوکی اگر وجود ندارد
os.makedirs("modules", exist_ok=True)
if not os.path.exists(COOKIE_FILE):
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        f.write("# Paste YouTube cookies here in Netscape format\n")

# پوشه دانلود
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# تشخیص URL
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

    # تنظیمات yt-dlp
    ydl_opts = {
        "cookiefile": COOKIE_FILE,      # ← استفاده از کوکی‌های تو
        "quiet": True,
        "format": "bestvideo+bestaudio/best",
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
        "noplaylist": True
    }

    try:
        # دانلود ویدیو
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        title = info.get("title", "YouTube Video")

        # ارسال ویدیو
        await msg.edit_text("⬇ در حال ارسال ویدیو...")
        await update.message.reply_video(
            video=open(filename, "rb"),
            caption=f"📥 {title}"
        )

        # تبدیل فایل به MP3
        mp3_file = filename.rsplit('.', 1)[0] + ".mp3"
        os.system(f'ffmpeg -i "{filename}" -vn -ab 192k "{mp3_file}" -y')

        # ارسال صوت
        await update.message.reply_audio(
            audio=open(mp3_file, "rb"),
            caption=f"🎵 {title}"
        )

        # پاکسازی
        os.remove(filename)
        os.remove(mp3_file)

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود یوتیوب:\n{e}")
