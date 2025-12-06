# modules/instagram_handler.py
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


async def instagram_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر اختصاصی دانلود اینستاگرام"""
    if not update.message or not update.message.text:
        return

    url = update.message.text.strip()

    # فقط لینک‌های اینستاگرام
    if "instagram.com" not in url:
        return

    chat_id = update.effective_chat.id
    msg = await update.message.reply_text("⬇️ در حال دانلود از Instagram ...")

    # جلوگیری از دانلود عکس‌ها
    if "/p/" in url and not any(x in url for x in ["/reel/", "/tv/"]):
        await msg.edit_text("❌ این لینک عکس است و پشتیبانی نمی‌شود.")
        return

    # ریدایرکت لینک کوتاه
    try:
        resp = requests.get(url, allow_redirects=True)
        url = resp.url
    except:
        pass

    # تنظیمات دقیق yt_dlp مخصوص اینستاگرام
    ydl_opts = {
        "quiet": True,
        "format": "best",
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
        "noplaylist": False,
        "merge_output_format": "mp4",
        "ignoreerrors": True,
        "extract_flat": False
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        if not info:
            await msg.edit_text("❌ امکان دانلود این پست وجود ندارد.")
            return

        # === حالت چند ویدیو (Carousel) ===
        if info.get("entries"):
            for item in info["entries"]:
                filename = ydl.prepare_filename(item)
                if os.path.exists(filename):
                    await context.bot.send_video(chat_id, filename)
                    os.remove(filename)
            await msg.delete()
            return

        # === حالت تک ویدیو ===
        filename = ydl.prepare_filename(info)

        await context.bot.send_video(chat_id, filename)

        # حذف فایل
        if os.path.exists(filename):
            os.remove(filename)

        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود از اینستاگرام:\n{e}")
