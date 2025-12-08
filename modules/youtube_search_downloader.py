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

# مطمئن شو پوشه و فایل کوکی وجود دارد
os.makedirs("modules", exist_ok=True)
if not os.path.exists(COOKIE_FILE):
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        f.write("# Paste YouTube cookies here in Netscape format\n")

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# تشخیص لینک
URL_RE = re.compile(r"(https?://[^\s]+)")

# ThreadPool برای اجرای yt-dlp بدون هنگ
executor = ThreadPoolExecutor(max_workers=3)


# ================================
#  تابع سینک دانلود صوت (داخل Thread)
# ================================
def _download_audio_sync(query: str, is_search: bool):
    """
    اگر is_search = True باشد:
        query = متن آهنگ → ytsearch1:...
    اگر is_search = False باشد:
        query = لینک مستقیم یوتیوب
    خروجی: (info_dict, mp3_path)
    """
    ydl_opts = {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "format": "bestaudio/best",          # فقط صوت
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
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        if is_search:
            search_url = f"ytsearch1:{query}"
            info = ydl.extract_info(search_url, download=True)
            if "entries" in info:
                info = info["entries"][0]
        else:
            info = ydl.extract_info(query, download=True)

        original_filename = ydl.prepare_filename(info)

    base, _ = os.path.splitext(original_filename)
    mp3_file = base + ".mp3"

    if not os.path.exists(mp3_file):
        raise RuntimeError("فایل MP3 بعد از دانلود پیدا نشد.")

    return info, mp3_file


# ================================
#  تابع سینک دانلود ویدیو (داخل Thread)
# ================================
def _download_video_sync(url: str):
    """
    دانلود ویدیو با کیفیت حداکثر 720p و خروجی MP4
    خروجی: (info_dict, video_path)
    """
    ydl_opts = {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        # ویدیو تا 720p + صدای بهترین کیفیت
        "format": "bv*[height<=720]+ba/best[height<=720]/best",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
        "prefer_ffmpeg": True,
        "cachedir": False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    if not os.path.exists(filename):
        raise RuntimeError("فایل ویدیو بعد از دانلود پیدا نشد.")

    return info, filename


# ================================
# هندلر اصلی برای ربات
#  - جستجو: "دانلود آهنگ / اهنگ / آهنگ ..."
#  - لینک: هر پیام حاوی لینک youtube / youtu.be  → ویدیو
# ================================
async def youtube_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    # -----------------------------
    # 1) حالت جستجو "دانلود آهنگ ..."
    # -----------------------------
    is_music_search = (
        text.startswith("دانلود آهنگ")
        or text.startswith("اهنگ")
        or text.startswith("آهنگ")
    )

    if is_music_search:
        # حذف کلمات شروع
        search_text = (
            text.replace("دانلود آهنگ", "")
            .replace("اهنگ", "")
            .replace("آهنگ", "")
            .strip()
        )

        if len(search_text) < 2:
            await update.message.reply_text("❌ لطفاً نام آهنگ یا خواننده را بنویس.")
            return

        msg = await update.message.reply_text(
            f"🎧 در حال جستجو در یوتیوب برای:\n🔎 <b>{search_text}</b>",
            parse_mode="HTML",
        )

        loop = asyncio.get_running_loop()
        try:
            info, mp3_path = await loop.run_in_executor(
                executor, _download_audio_sync, search_text, True
            )
        except Exception as e:
            await msg.edit_text(f"❌ خطا در دانلود:\n{e}")
            return

        title = info.get("title", "Music")

        await msg.edit_text("⬇ در حال ارسال فایل صوتی...")

        try:
            with open(mp3_path, "rb") as f:
                await update.message.reply_audio(
                    audio=f,
                    title=title,
                    caption=f"🎵 {title}",
                )
        finally:
            if os.path.exists(mp3_path):
                try:
                    os.remove(mp3_path)
                except:
                    pass

        return  # این پیام برای جستجوی آهنگ بود، پس دیگه ادامه نمی‌دیم

    # -----------------------------
    # 2) حالت لینک مستقیم یوتیوب → ویدیو
    # -----------------------------
    m = URL_RE.search(text)
    if not m:
        return  # نه جستجوی آهنگ بود، نه لینک → هیچی

    url = m.group(1)
    if "youtube.com" not in url and "youtu.be" not in url:
        return

    msg = await update.message.reply_text("📥 در حال دانلود ویدیو از یوتیوب...")

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
            try:
                os.remove(video_path)
            except:
                pass
