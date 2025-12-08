# modules/youtube_downloader.py
import os
import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes
import re

# مسیر فایل کوکی
COOKIE_FILE = "modules/youtube_cookie.txt"

# ساخت پوشه‌ها
os.makedirs("modules", exist_ok=True)
os.makedirs("downloads", exist_ok=True)

if not os.path.exists(COOKIE_FILE):
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        f.write("# Paste YouTube cookies here in Netscape format\n")

DOWNLOAD_FOLDER = "downloads"

# regex تشخیص لینک
URL_RE = re.compile(r"(https?://[^\s]+)")


async def youtube_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    match = URL_RE.search(text)
    if not match:
        return

    url = match.group(1)
    if "youtube.com" not in url and "youtu.be" not in url:
        return

    msg = await update.message.reply_text("📥 در حال پردازش لینک یوتیوب... لطفاً صبر کنید.")

    # تنظیمات yt-dlp
    ydl_opts = {
        "cookiefile": COOKIE_FILE,
        "quiet": True,

        # ✨ مهم‌ترین بخش:
        # دانلود همان فایل اصلی یوتیوب (Video + Audio ترکیب‌شده)
        "format": "best[acodec!=none][vcodec!=none]",

        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
        "noplaylist": True,

        # حذف challenge یوتیوب (بدون نیاز به Nodejs)
        "extractor_args": {
            "youtube": {
                "player_client": ["android"],
            }
        },
    }

    try:
        # دانلود ویدیو
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        title = info.get("title", "YouTube Video")
        video_id = info.get("id")
        video_ext = info.get("ext", "mp4")

        video_file = f"{DOWNLOAD_FOLDER}/{video_id}.{video_ext}"

        # بررسی حجم قبل از ارسال (Heroku محدود است)
        if os.path.getsize(video_file) > 180 * 1024 * 1024:
            await msg.edit_text("⚠ حجم ویدیو خیلی بزرگ است. امکان ارسال وجود ندارد.")
            os.remove(video_file)
            return

        # ارسال ویدیو
        await msg.edit_text("⬇ در حال ارسال فایل...")
        await update.message.reply_video(
            video=open(video_file, "rb"),
            caption=f"📥 {title}"
        )

        # پاکسازی
        os.remove(video_file)

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود:\n{e}")
