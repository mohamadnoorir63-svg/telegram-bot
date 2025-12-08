# modules/youtube_search_downloader.py
import os
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor

import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes

# ================================
# تنظیم اولیه
# ================================
COOKIE_FILE = "modules/youtube_cookie.txt"

os.makedirs("modules", exist_ok=True)
if not os.path.exists(COOKIE_FILE):
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        f.write("# Paste YouTube cookies here in Netscape format\n")

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

URL_RE = re.compile(r"(https?://[^\s]+)")

# ThreadPool → جلوگیری از هنگ شدن ربات
executor = ThreadPoolExecutor(max_workers=5)


# ================================
# تابع دانلود صوت
# ================================
def _download_audio_sync(query: str, is_search: bool):

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
        "prefer_ffmpeg": True,
        "cachedir": False,
        "concurrent_fragment_downloads": 5,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        if is_search:
            query = f"ytsearch1:{query}"

        info = ydl.extract_info(query, download=True)

        if "entries" in info:
            info = info["entries"][0]

        filename = ydl.prepare_filename(info)

    base, _ = os.path.splitext(filename)
    mp3_file = base + ".mp3"

    if not os.path.exists(mp3_file):
        raise RuntimeError("MP3 file not found.")

    return info, mp3_file


# ================================
# تابع دانلود ویدیو
# ================================
def _download_video_sync(url: str):

    ydl_opts = {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "format": "bv*[height<=720]+ba/best",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "prefer_ffmpeg": True,
        "cachedir": False,
        "concurrent_fragment_downloads": 5,
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    if not os.path.exists(filename):
        raise RuntimeError("Video file not found.")

    return info, filename


# ================================
# هندلر اصلی ربات
# ================================
async def youtube_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip().lower()

    # ================================
    # دستورات چندزبانه جستجوی آهنگ
    # ================================
    search_cmds = [
        "دانلود آهنگ", "اهنگ", "آهنگ",
        "تحميل اغنية", "اغنية", "أغنية",
        "download song", "music", "song"
    ]

    is_music_search = any(text.startswith(cmd) for cmd in search_cmds)

    # -----------------------------
    # حالت جستجو آهنگ
    # -----------------------------
    if is_music_search:

        clean_text = text
        for cmd in search_cmds:
            clean_text = clean_text.replace(cmd, "")
        clean_text = clean_text.strip()

        if len(clean_text) < 2:
            await update.message.reply_text("❌ لطفاً نام آهنگ را وارد کنید.")
            return

        msg = await update.message.reply_text(
            f"🎧 در حال جستجو و دانلود آهنگ:\n🔎 <b>{clean_text}</b>",
            parse_mode="HTML",
        )

        loop = asyncio.get_running_loop()

        try:
            info, mp3_file = await loop.run_in_executor(
                executor, _download_audio_sync, clean_text, True
            )
        except Exception as e:
            await msg.edit_text(f"❌ خطا در دانلود آهنگ:\n{e}")
            return

        title = info.get("title", clean_text)

        await msg.edit_text("⬇ در حال ارسال فایل صوتی...")

        try:
            with open(mp3_file, "rb") as f:
                await update.message.reply_audio(
                    audio=f,
                    title=title,
                    caption=f"🎵 {title}",
                )
        finally:
            if os.path.exists(mp3_file):
                os.remove(mp3_file)

        return

    # -----------------------------
    # حالت لینک → دانلود ویدیو
    # -----------------------------
    match = URL_RE.search(update.message.text)
    if not match:
        return

    url = match.group(1)

    if "youtube.com" not in url and "youtu.be" not in url:
        return

    msg = await update.message.reply_text("📥 در حال دانلود ویدیو...")

    loop = asyncio.get_running_loop()

    try:
        info, video_path = await loop.run_in_executor(
            executor, _download_video_sync, url
        )
    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود ویدیو:\n{e}")
        return

    title = info.get("title", "YouTube Video")

    await msg.edit_text("⬇ در حال ارسال ویدیو...")

    try:
        with open(video_path, "rb") as f:
            await update.message.reply_video(video=f, caption=f"🎬 {title}")
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)
