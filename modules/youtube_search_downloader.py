import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes
import os
import re

COOKIE_FILE = "modules/youtube_cookie.txt"
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

async def youtube_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # فقط اگر کاربر گفت: دانلود آهنگ ...
    if not text.startswith("دانلود آهنگ"):
        return

    query = text.replace("دانلود آهنگ", "").strip()

    if len(query) < 2:
        return await update.message.reply_text("🎵 لطفاً نام آهنگ را بنویس مثال:\nدانلود آهنگ سکوتم را به باران هدیه کردم")

    msg = await update.message.reply_text(f"🎧 در حال جستجو برای: {query}")

    try:
        # جستجو در یوتیوب
        search_url = f"ytsearch:{query}"

        ydl_opts = {
            "quiet": True,
            "cookiefile": COOKIE_FILE,
            "format": "bestaudio/best",
            "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s"
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_url, download=True)
            entry = info["entries"][0]  # اولین نتیجه
            filename = ydl.prepare_filename(entry)

        title = entry.get("title", "Music")

        await msg.edit_text("⬇ ارسال فایل صوتی...")

        await update.message.reply_audio(
            audio=open(filename, "rb"),
            caption=f"🎵 {title}"
        )

        os.remove(filename)

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود:\n{e}")
