import os
import shutil
import subprocess
import requests
import yt_dlp
import asyncio
from concurrent.futures import ThreadPoolExecutor
from telegram import Update
from telegram.ext import ContextTypes
import uuid

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
executor = ThreadPoolExecutor(max_workers=2)

async def convert_to_mp3(video_path: str) -> str:
    mp3_path = video_path.rsplit(".", 1)[0] + ".mp3"
    if not shutil.which("ffmpeg"):
        return None
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-ab", "192k", "-ar", "44100",
        "-f", "mp3", mp3_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return mp3_path

async def download_video(url: str, ydl_opts: dict):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=True))

async def media_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    chat_id = update.effective_chat.id
    msg = await update.message.reply_text("⬇️ در حال پردازش رسانه ...")

    try:
        # ریدایرکت لینک کوتاه TikTok
        if "vm.tiktok.com" in url or "vt.tiktok.com" in url:
            try:
                resp = requests.get(url, allow_redirects=True)
                url = resp.url
            except Exception as e:
                await msg.edit(f"❌ خطا در ریدایرکت لینک: {e}")
                return

        # بررسی عکس‌ها
        if "/photo/" in url or "/media/?size=l" in url:
            await msg.edit("❌ عکس‌ها پشتیبانی نمی‌شوند.")
            return

        # نام فایل یکتا برای جلوگیری از تداخل cache
        unique_id = str(uuid.uuid4())
        ydl_opts = {
            "format": "mp4",
            "outtmpl": os.path.join(DOWNLOAD_FOLDER, f"{unique_id}.%(ext)s"),
            "quiet": True,
            "noplaylist": True,
            "merge_output_format": "mp4",
            "rm_cache_dir": True,  # پاکسازی کش yt-dlp
            "http_headers": {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        }

        info = await download_video(url, ydl_opts)
        if not info:
            await msg.edit("❌ ویدیو پیدا نشد یا پشتیبانی نمی‌شود.")
            return

        filename = yt_dlp.YoutubeDL(ydl_opts).prepare_filename(info)

        # ارسال ویدیو
        await context.bot.send_video(chat_id, filename, caption=f"🎬 {info.get('title','Video')}")

        # ارسال صوت
        mp3_path = await convert_to_mp3(filename)
        if mp3_path and os.path.exists(mp3_path):
            await context.bot.send_audio(chat_id, mp3_path, caption="🎵 صوت ویدیو")
            os.remove(mp3_path)

        os.remove(filename)

    except Exception as e:
        await msg.edit(f"❌ خطا در دانلود رسانه: {e}")
    finally:
        try: await msg.delete()
        except: pass
