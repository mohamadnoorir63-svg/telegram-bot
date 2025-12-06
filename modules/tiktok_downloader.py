# modules/media_handler.py
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
    """دانلود ویدیو TikTok، Instagram و YouTube و ارسال صوت، پیام خطا برای عکس"""
    if not update.message or not update.message.text:
        return  # پیام خالی یا غیرمتنی → نادیده گرفته شود

    url = update.message.text.strip()
    chat_id = update.effective_chat.id
    msg = await update.message.reply_text("⬇️ در حال پردازش رسانه ...")

    # فقط لینک‌های معتبر
    if not any(x in url for x in ["tiktok.com", "instagram.com", "youtu.be", "youtube.com"]):
        await msg.edit_text("❌ این لینک پشتیبانی نمی‌شود.")
        return

    # ریدایرکت لینک کوتاه TikTok و Instagram
    if any(x in url for x in ["vm.tiktok.com", "vt.tiktok.com", "instagram.com/p/", "instagram.com/reel/"]):
        try:
            resp = requests.get(url, allow_redirects=True)
            url = resp.url
        except Exception as e:
            await msg.edit_text(f"❌ خطا در ریدایرکت لینک: {e}")
            return

    # بررسی عکس‌ها
    if ("/photo/" in url) or ("instagram.com/p/" in url and "/media/" in url):
        await msg.edit_text("❌ عکس‌ها پشتیبانی نمی‌شوند.")
        return

    # تنظیمات yt-dlp
    ydl_opts = {
        "format": "mp4",
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
        "quiet": True,
        "noplaylist": False,
        "merge_output_format": "mp4",
        "ignoreerrors": True,
        "playlistend": 10,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            if not info:
                await msg.edit_text("❌ لینک پشتیبانی نمی‌شود یا ویدیو قابل دانلود نیست.")
                return

            entries = info.get("entries")
            if entries:
                # چند ویدیو (Instagram Carousel یا YouTube Playlist)
                for video_info in entries:
                    filename = ydl.prepare_filename(video_info)
                    if os.path.exists(filename):
                        await context.bot.send_video(chat_id, filename, caption=f"🎬 {video_info.get('title','Video')}")
                        mp3_path = await convert_to_mp3(filename)
                        if mp3_path and os.path.exists(mp3_path):
                            await context.bot.send_audio(chat_id, mp3_path, caption="🎵 صوت ویدیو")
                            os.remove(mp3_path)
                        os.remove(filename)
            else:
                # یک ویدیو
                filename = ydl.prepare_filename(info)
                await context.bot.send_video(chat_id, filename, caption=f"🎬 {info.get('title','Video')}")
                mp3_path = await convert_to_mp3(filename)
                if mp3_path and os.path.exists(mp3_path):
                    await context.bot.send_audio(chat_id, mp3_path, caption="🎵 صوت ویدیو")
                    os.remove(mp3_path)
                os.remove(filename)

            await msg.delete()

    except yt_dlp.utils.DownloadError:
        await msg.edit_text("❌ لینک پشتیبانی نمی‌شود یا ویدیو قابل دانلود نیست.")
    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود رسانه: {e}")
