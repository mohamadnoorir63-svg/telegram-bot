# modules/youtube_search_downloader.py
import os
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor

import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes

# ================================
# تنظیمات اولیه
# ================================
COOKIE_FILE = "modules/youtube_cookie.txt"

os.makedirs("modules", exist_ok=True)
if not os.path.exists(COOKIE_FILE):
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        f.write("# Paste YouTube cookies here in Netscape format\n")

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

URL_RE = re.compile(r"(https?://[^\s]+)")

executor = ThreadPoolExecutor(max_workers=5)   # سرعت ↑↑↑


# ================================
# دانلود صوت (Thread)
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
        "concurrent_fragment_downloads": 5,  # سرعت ↑↑↑
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        if is_search:
            query = f"ytsearch1:{query}"
        info = ydl.extract_info(query, download=True)
        if "entries" in info:
            info = info["entries"][0]

        file_original = ydl.prepare_filename(info)

    base, _ = os.path.splitext(file_original)
    mp3_path = base + ".mp3"

    if not os.path.exists(mp3_path):
        raise RuntimeError("MP3 پیدا نشد (تبدیل شکست خورده).")

    return info, mp3_path


# ================================
# دانلود ویدیو (Thread)
# ================================
def _download_video_sync(url: str):

    ydl_opts = {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "format": "bv*[height<=720]+ba/best",  # ویدیو + صدا
        "merge_output_format": "mp4",
        "noplaylist": True,
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
        "prefer_ffmpeg": True,
        "cachedir": False,
        "concurrent_fragment_downloads": 5,  # سرعت بالاتر
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    if not os.path.exists(filename):
        raise RuntimeError("فایل ویدیو پیدا نشد.")

    return info, filename


# ================================
# هندلر اصلی
# ================================
async def youtube_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    # ================================
    #  تشخیص دستورات سه‌زبانه جستجوی آهنگ
    #  فارسی + عربی + انگلیسی
    # ================================
    search_commands = ["دانلود آهنگ", "اهنگ", "آهنگ",
                       "تحميل اغنية", "اغنية", "أغنية",
                       "download song", "music", "song"]

    is_music_search = any(text.lower().startswith(cmd) for cmd in search_commands)

    # -----------------------------
    # حالت جستجو آهنگ
    # -----------------------------
    if is_music_search:

        # پاکسازی فرمان از متن
        clean_text = text.lower()
        for cmd in search_commands:
            clean_text = clean_text.replace(cmd, "")
        clean_text = clean_text.strip()

        if len(clean_text) < 2:
            await update.message.reply_text("❌ لطفاً نام آهنگ را بنویس.")
            return

        msg = await update.message.reply_text(
            f"🎧 در حال جستجو و دانلود آهنگ…\n🔎 <b>{clean_text}</b>",
            parse_mode="HTML",
        )

        loop = asyncio.get_running_loop()
        try:
            info, mp3_path = await loop.run_in_executor(
                executor, _download_audio_sync, clean_text, True
            )
        except Exception as e:
            await msg.edit_text(f"❌ خطا در دانلود:\n{e}")
            return

        title = info.get("title", clean_text)

        await msg.edit_text("⬇ در حال ارسال فایل صوتی...")

        # ارسال فایل
        try:
            with open(mp3_path, "rb") as f:
                await update.message.reply_audio(
                    audio=f,
                    caption=f"🎵 {title}",
                    title=title,
                )
        finally:
            if os.path.exists(mp3_path):
                os.remove(mp3_path)

        return

    # -----------------------------
    # حالت لینک مستقیم یوتیوب → ویدیو
    # -----------------------------
    m = URL_RE.search(text)
    if not m:
        return

    url = m.group(1)

    if "youtube.com" not in url and "youtu.be" not in url:
        return

    msg = await update.message.reply_text("📥 در حال دانلود ویدیو...")

    loop = asyncio.get_running_loop()
    try:
        info, video_path = await loop.run_in_executor(
            executor, _download_video_sync, url
        )
    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود:\n{e}")
        return

    title = info.get("title", "YouTube Video")

    await msg.edit_text("⬇ در حال ارسال ویدیو...")

    try:
        with open(video_path, "rb") as f:
            await update.message.reply_video(
                video=f,
                caption=f"🎬 {title}",
            )
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)
