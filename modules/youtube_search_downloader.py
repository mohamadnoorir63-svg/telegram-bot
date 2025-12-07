# modules/youtube_search_downloader.py
import os
import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes
import re

# مسیر کوکی یوتیوب
COOKIE_FILE = "modules/youtube_cookie.txt"

# مسیر دانلود‌ها
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# الگوی جستجو
SEARCH_QUERY_RE = re.compile(r"(دانلود آهنگ|دانلود موزیک|آهنگ|موزیک)\s+(.*)", re.IGNORECASE)


async def youtube_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    match = SEARCH_QUERY_RE.search(text)
    if not match:
        return

    query = match.group(2)   # نام آهنگ
    msg = await update.message.reply_text(f"🔍 در حال جستجو برای:\n🎵 {query}")

    # گزینه‌های yt-dlp
    ydl_opts = {
        "quiet": True,
        "cookiefile": COOKIE_FILE,
        "format": "best",
        "default_search": "ytsearch1",
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s"
    }

    try:
        # استخراج اطلاعات از یوتیوب
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            if "entries" in info:
                info = info["entries"][0]

            filename = ydl.prepare_filename(info)

        title = info.get("title", "Music")

        # ارسال ویدیو
        await msg.edit_text("⬇ در حال ارسال ویدیو...")
        await update.message.reply_video(
            video=open(filename, "rb"),
            caption=f"🎬 {title}"
        )

        # ساخت نسخه صوتی MP3
        mp3_file = filename.rsplit(".", 1)[0] + ".mp3"
        os.system(f'ffmpeg -i "{filename}" -vn -ab 192k "{mp3_file}" -y')

        # ارسال فایل صوتی
        await update.message.reply_audio(
            audio=open(mp3_file, "rb"),
            caption=f"🎵 نسخه صوتی:\n{title}"
        )

        # پاکسازی
        os.remove(filename)
        os.remove(mp3_file)

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود:\n{e}")
