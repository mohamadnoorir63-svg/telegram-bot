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
    """جستجو و دانلود آهنگ از SoundCloud با متن یا بخشی از شعر"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    chat_id = update.effective_chat.id

    if not text.startswith(("آهنگ ", "موزیک ")):
        return

    query = text.split(" ", 1)[1].strip()
    if not query:
        await update.message.reply_text("❌ لطفاً نام آهنگ یا بخشی از شعر را وارد کنید.")
        return

    msg = await update.message.reply_text("🔍 در حال جستجو در SoundCloud...")

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # فقط جستجو (بدون دانلود)
            info = ydl.extract_info(f"scsearch5:{query}", download=False)

            if not info or "entries" not in info or not info["entries"]:
                await msg.edit_text("❌ آهنگ پیدا نشد.")
                return

            # اولین نتیجه نزدیک‌ترین آهنگ
            track = info["entries"][0]
            url = track.get("webpage_url")

            # دانلود آهنگ واقعی
            info2 = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info2)

            # تبدیل به mp3 و ارسال
            mp3_path = await convert_to_mp3(filename)
            if mp3_path and os.path.exists(mp3_path):
                await context.bot.send_audio(chat_id, mp3_path, caption=f"🎵 {track.get('title','SoundCloud')}")
                os.remove(mp3_path)
            else:
                await context.bot.send_document(chat_id, filename, caption=f"🎵 {track.get('title','SoundCloud')}")

            if os.path.exists(filename):
                os.remove(filename)

        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود موزیک:\n{e}")
