# modules/youtube_search_downloader.py
import os
import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes
import re

COOKIE_FILE = "modules/youtube_cookie.txt"

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


async def youtube_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()

    # فقط اگر کاربر نوشته "دانلود آهنگ ..."
    if not (query.startswith("دانلود آهنگ") or query.startswith("اهنگ") or query.startswith("آهنگ")):
        return

    search_text = (
        query.replace("دانلود آهنگ", "")
             .replace("آهنگ", "")
             .replace("اهنگ", "")
             .strip()
    )

    if len(search_text) < 2:
        return await update.message.reply_text("❌ لطفاً نام آهنگ را بنویس!")

    msg = await update.message.reply_text(f"🎧 در حال جستجو برای:\n🔎 {search_text}")

    # ============================
    # 1️⃣ جستجو در یوتیوب
    # ============================
    search_url = f"ytsearch1:{search_text}"

    ydl_opts = {
        "quiet": True,
        "cookiefile": COOKIE_FILE,
        "format": "bestaudio[ext=webm]/bestaudio",  # 👈 همیشه موجود
        "noplaylist": True,
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_url, download=True)
            if "entries" in info:
                info = info["entries"][0]

            filename = ydl.prepare_filename(info)

        title = info.get("title", "Music")

        # مسیر خروجی MP3
        mp3_file = filename.rsplit(".", 1)[0] + ".mp3"

        # ============================
        # 2️⃣ تبدیل صوت به MP3
        # ============================
        os.system(f'ffmpeg -i "{filename}" -vn -codec:a libmp3lame -b:a 192k "{mp3_file}" -y')

        await msg.edit_text("⬇ در حال ارسال فایل صوتی...")

        await update.message.reply_audio(
            audio=open(mp3_file, "rb"),
            title=title,
            caption=f"🎵 {title}"
        )

        # حذف فایل‌ها
        os.remove(filename)
        os.remove(mp3_file)

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود:\n{e}")
