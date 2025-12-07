import re
import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes

URL_RE = re.compile(r"(https?://[^\s]+)")

async def instagram_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.strip()
    match = URL_RE.search(text)

    if not match:
        return

    url = match.group(1)

    if "instagram.com" not in url:
        return

    msg = await update.message.reply_text("📥 در حال بررسی لینک اینستاگرام...")

    ydl_opts = {
        "cookiefile": "instagram_cookies.txt",   # ← این مهم‌ترین بخش است
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "quiet": True,
        "format": "best",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # ارسال فایل
        await update.message.reply_video(
            video=open(filename, "rb"),
            caption="📥 ویدیو با موفقیت دانلود شد!"
        )

        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ نتوانستم دانلود کنم.\n🔁 دوباره تلاش کن!\n\n⚠️ خطا: {e}")
