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
    """دانلود فقط Instagram"""
    if not update.message or not update.message.text:
        return  # جلوگیری از پردازش پیام‌های خالی

    url = update.message.text.strip()
    chat_id = update.effective_chat.id

    # فقط لینک‌های اینستاگرام
    if "instagram.com" not in url:
        return

    msg = await update.message.reply_text("⬇️ در حال دانلود از Instagram ...")

    # جلوگیری از دانلود عکس
    if "/p/" in url and "/photo/" in url:
        await msg.edit_text("❌ عکس‌های اینستاگرام پشتیبانی نمی‌شوند.")
        return

    # ریدایرکت لینک‌های کوتاه
    try:
        resp = requests.get(url, allow_redirects=True)
        url = resp.url
    except Exception:
        pass

    # تنظیمات yt-dlp
    ydl_opts = {
        "format": "mp4",
        "quiet": True,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
        "merge_output_format": "mp4",
        "noplaylist": False,
        "ignoreerrors": True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            if info is None:
                await msg.edit_text("❌ امکان دانلود این پست وجود ندارد.")
                return

            # اگر چند ویدیو باشد (Carousel)
            if "entries" in info and info["entries"]:
                for v in info["entries"]:
                    filename = ydl.prepare_filename(v)
                    if os.path.exists(filename):
                        await context.bot.send_video(chat_id, filename, caption=f"🎬 {v.get('title', 'Instagram Video')}")
                        
                        # ساخت mp3
                        mp3_path = await convert_to_mp3(filename)
                        if mp3_path and os.path.exists(mp3_path):
                            await context.bot.send_audio(chat_id, mp3_path, caption="🎵 صوت ویدیو")
                            os.remove(mp3_path)

                        os.remove(filename)

            else:
                # تک ویدیو
                filename = ydl.prepare_filename(info)
                await context.bot.send_video(chat_id, filename, caption=f"🎬 {info.get('title', 'Instagram Video')}")

                mp3_path = await convert_to_mp3(filename)
                if mp3_path and os.path.exists(mp3_path):
                    await context.bot.send_audio(chat_id, mp3_path, caption="🎵 صوت ویدیو")
                    os.remove(mp3_path)

                os.remove(filename)

        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود از اینستاگرام: {e}")
