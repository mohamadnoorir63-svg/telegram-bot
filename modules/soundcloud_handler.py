# modules/soundcloud_handler.py
import os
import shutil
import subprocess
import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

async def convert_to_mp3(video_path: str) -> str:
    """تبدیل ویدیو/آهنگ به MP3"""
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

async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """جستجو و دانلود آهنگ از SoundCloud"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    chat_id = update.effective_chat.id

    if not text.startswith("آهنگ "):
        return

    query = text.replace("/موزیک ", "", 1).strip()
    if not query:
        await update.message.reply_text("❌ لطفاً نام آهنگ را وارد کنید.")
        return

    msg = await update.message.reply_text("🔍 در حال جستجو در SoundCloud...")

    # yt-dlp تنظیمات
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # جستجو روی SoundCloud
            info = ydl.extract_info(f"scsearch:{query}", download=True)

            if not info or "entries" not in info or not info["entries"]:
                await msg.edit_text("❌ آهنگ پیدا نشد.")
                return

            # اولین نتیجه
            track = info["entries"][0]
            filename = ydl.prepare_filename(track)

            # ارسال ویدیو/صوت
            mp3_path = await convert_to_mp3(filename)
            if mp3_path and os.path.exists(mp3_path):
                await context.bot.send_audio(chat_id, mp3_path, caption=f"🎵 {track.get('title','SoundCloud')}")
                os.remove(mp3_path)
            else:
                # اگر تبدیل نشد، فایل اصلی ارسال می‌شود
                await context.bot.send_document(chat_id, filename, caption=f"🎵 {track.get('title','SoundCloud')}")

            if os.path.exists(filename):
                os.remove(filename)

        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود موزیک:\n{e}")
