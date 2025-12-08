# ================================
#   YOUTUBE SEARCH MP3 DOWNLOADER
#       (NO FREEZE VERSION)
# ================================

import os
import yt_dlp
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
from telegram import Update
from telegram.ext import ContextTypes

COOKIE_FILE = "modules/youtube_cookie.txt"
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

executor = ThreadPoolExecutor(max_workers=3)

# -------------------------------
# اجرای yt-dlp داخل Thread (جلوگیری از هنگ)
# -------------------------------
def yt_search_and_download(query):
    search_url = f"ytsearch1:{query}"

    ydl_opts = {
        "quiet": True,
        "cookiefile": COOKIE_FILE,
        "format": "bestaudio/best",
        "noplaylist": True,
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }
        ]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_url, download=True)

        if "entries" in info:
            info = info["entries"][0]

        video_id = info["id"]
        title = info.get("title", "Music")
        mp3_file = f"{DOWNLOAD_FOLDER}/{video_id}.mp3"

        return title, mp3_file


# -------------------------------
# هندلر اصلی دانلود آهنگ
# -------------------------------
async def youtube_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()

    # دستورهای مجاز
    if not (
        text.startswith("دانلود آهنگ")
        or text.startswith("اهنگ")
        or text.startswith("آهنگ")
    ):
        return

    # حذف کلمات اضافی
    query = (
        text.replace("دانلود آهنگ", "")
        .replace("اهنگ", "")
        .replace("آهنگ", "")
        .strip()
    )

    if len(query) < 2:
        return await update.message.reply_text("❌ لطفاً نام آهنگ را وارد کنید.")

    msg = await update.message.reply_text(
        f"🎧 در حال جستجو در یوتیوب...\n🔎 <b>{query}</b>",
        parse_mode="HTML"
    )

    # ---------------------------
    # اجرای yt-dlp داخل Thread
    # ---------------------------
    loop = asyncio.get_running_loop()
    try:
        title, mp3_file = await loop.run_in_executor(
            executor,
            yt_search_and_download,
            query
        )
    except Exception as e:
        return await msg.edit_text(f"❌ خطا در دانلود:\n`{e}`")

    # ---------------------------
    # ارسال فایل صوتی
    # ---------------------------
    await msg.edit_text("⬇ در حال ارسال فایل صوتی...")

    try:
        with open(mp3_file, "rb") as f:
            await update.message.reply_audio(
                audio=f,
                caption=f"🎵 {title}",
                title=title
            )
    finally:
        if os.path.exists(mp3_file):
            os.remove(mp3_file)
