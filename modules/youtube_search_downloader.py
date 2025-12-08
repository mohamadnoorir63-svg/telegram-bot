# modules/youtube_search_downloader.py
import os
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor

import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes

COOKIE_FILE = "modules/youtube_cookie.txt"
os.makedirs("modules", exist_ok=True)
if not os.path.exists(COOKIE_FILE):
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        f.write("# Paste YouTube cookies here in Netscape format\n")

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

URL_RE = re.compile(r"(https?://[^\s]+)")

executor = ThreadPoolExecutor(max_workers=3)


# ==========================
#  دانلود صوتی برای جستجو
# ==========================
def _download_audio_sync(query, is_search):
    ydl_opts = {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "format": "bestaudio/best",
        "noplaylist": True,
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        if is_search:
            info = ydl.extract_info(f"ytsearch1:{query}", download=True)
            if "entries" in info:
                info = info["entries"][0]
        else:
            info = ydl.extract_info(query, download=True)

        base = ydl.prepare_filename(info).rsplit(".", 1)[0]
        mp3_path = base + ".mp3"

    return info, mp3_path


# ==========================
#  دانلود ویدیو برای لینک
# ==========================
def _download_video_sync(url):
    ydl_opts = {
        "cookiefile": COOKIE_FILE,
        "quiet": True,

        # 🎥 کیفیت مناسب ویدیو (بدون SABR مشکل‌دار)
        "format": "bestvideo[height<=720]+bestaudio/best[height<=720]/best",

        "merge_output_format": "mp4",
        "noplaylist": True,
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    return info, filename


# ================================
#     هندلر اصلی
# ================================
async def youtube_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    # -------------------------
    # 🎵 حالت جستجو آهنگ
    # -------------------------
    if (
        text.startswith("دانلود آهنگ")
        or text.startswith("اهنگ")
        or text.startswith("آهنگ")
    ):
        search_text = (
            text.replace("دانلود آهنگ", "")
            .replace("اهنگ", "")
            .replace("آهنگ", "")
            .strip()
        )

        msg = await update.message.reply_text(
            f"🎧 جست‌وجوی آهنگ در یوتیوب...\n🔎 <b>{search_text}</b>",
            parse_mode="HTML",
        )

        loop = asyncio.get_running_loop()
        try:
            info, mp3_path = await loop.run_in_executor(
                executor, _download_audio_sync, search_text, True
            )
        except Exception as e:
            return await msg.edit_text(f"❌ خطا:\n{e}")

        title = info.get("title", "Music")

        await msg.edit_text("⬇ در حال ارسال فایل صوتی...")

        with open(mp3_path, "rb") as f:
            await update.message.reply_audio(audio=f, caption=f"🎵 {title}")

        os.remove(mp3_path)
        return

    # -------------------------
    # 🎥 حالت لینک مستقیم یوتیوب
    # -------------------------
    match = URL_RE.search(text)
    if not match:
        return

    url = match.group(1)
    if "youtube.com" not in url and "youtu.be" not in url:
        return

    msg = await update.message.reply_text("📥 در حال دانلود ویدیو... لطفاً صبر کنید.")

    loop = asyncio.get_running_loop()
    try:
        info, video_file = await loop.run_in_executor(
            executor, _download_video_sync, url
        )
    except Exception as e:
        return await msg.edit_text(f"❌ خطا در دانلود:\n{e}")

    title = info.get("title", "YouTube Video")

    await msg.edit_text("⬇ در حال ارسال ویدیو...")

    try:
        await update.message.reply_video(video=open(video_file, "rb"), caption=f"🎬 {title}")
    except Exception as e:
        await msg.edit_text(f"❌ ارسال ویدیو با خطا مواجه شد:\n{e}")
    finally:
        if os.path.exists(video_file):
            os.remove(video_file)
