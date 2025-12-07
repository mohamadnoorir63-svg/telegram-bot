import re
import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes

# Regex برای پیدا کردن لینک
URL_RE = re.compile(r"(https?://[^\s]+)")

COOKIE_FILE = "instagram_cookies.txt"   # ← فایل کوکی تو

async def instagram_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    match = URL_RE.search(text)

    if not match:
        return

    url = match.group(1)

    if "instagram.com" not in url:
        return

    msg = await update.message.reply_text("📥 در حال بررسی و دانلود از اینستاگرام...")

    # گزینه‌های yt-dlp با کوکی
    ydl_opts = {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "format": "best",
        "outtmpl": "downloads/%(id)s.%(ext)s",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        # ارسال فایل
        await update.message.reply_video(
            video=open(file_path, "rb"),
            caption="📥 ویدیو با موفقیت دانلود شد!"
        )

        await msg.delete()

    except Exception as e:
        await msg.edit_text(
            f"❌ نتوانستم دانلود کنم.\n🔁 دوباره تلاش کن!"
        )
