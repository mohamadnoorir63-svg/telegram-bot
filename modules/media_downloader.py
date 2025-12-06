import os
import shutil
import subprocess
import requests
import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

async def convert_to_mp3(video_path: str) -> str:
    """تبدیل ویدیو به MP3"""
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

async def media_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دانلود ویدیو TikTok و Instagram و ارسال صوت، پیام خطا برای عکس"""
    url = update.message.text.strip()
    chat_id = update.effective_chat.id
    msg = await update.message.reply_text("⬇️ در حال پردازش رسانه ...")

    # ریدایرکت لینک کوتاه TikTok
    if "vm.tiktok.com" in url or "vt.tiktok.com" in url:
        try:
            resp = requests.get(url, allow_redirects=True)
            url = resp.url
        except Exception as e:
            await msg.edit(f"❌ خطا در ریدایرکت لینک: {e}")
            return

    # بررسی عکس‌ها
    if "/photo/" in url or "instagram.com/p/" in url and "media/?size=l" in url:
        await msg.edit("❌ عکس‌ها پشتیبانی نمی‌شوند.")
        return

    # دانلود ویدیو با yt-dlp
    ydl_opts = {
        "format": "mp4",
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
        "quiet": True,
        "noplaylist": True,
        "merge_output_format": "mp4"
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # ارسال ویدیو
        await context.bot.send_video(chat_id, filename, caption=f"🎬 {info.get('title','Video')}")

        # ارسال صوت
        mp3_path = await convert_to_mp3(filename)
        if mp3_path and os.path.exists(mp3_path):
            await context.bot.send_audio(chat_id, mp3_path, caption="🎵 صوت ویدیو")
            os.remove(mp3_path)

        os.remove(filename)
        await msg.delete()

    except Exception as e:
        await msg.edit(f"❌ خطا در دانلود رسانه: {e}")
