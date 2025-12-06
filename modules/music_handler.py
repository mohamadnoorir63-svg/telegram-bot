# modules/music_handler.py
import os
import shutil
import subprocess
import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

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

# ----------------------------
# هندلر کامند /music
# ----------------------------
async def music_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ لطفا لینک یا نام آهنگ را بعد از /music بفرستید.\nمثال: /music https://www.youtube.com/watch?v=abc123xyz")
        return

    query = " ".join(context.args)
    chat_id = update.effective_chat.id
    msg = await update.message.reply_text(f"⬇️ در حال دانلود آهنگ: {query} ...")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
        "quiet": True,
        "noplaylist": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            if not info:
                await msg.edit_text("❌ آهنگ پیدا نشد یا قابل دانلود نیست.")
                return

            filename = ydl.prepare_filename(info).rsplit(".", 1)[0] + ".mp3"

        if os.path.exists(filename):
            await context.bot.send_audio(chat_id, filename, caption=f"🎵 {info.get('title', 'Music')}")
            os.remove(filename)
            await msg.delete()
        else:
            await msg.edit_text("❌ مشکلی پیش آمد، فایل پیدا نشد.")

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود آهنگ:\n{e}")
