# modules/music_handler.py
import os
import shutil
import subprocess
import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

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

async def music_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دانلود آهنگ از YouTube با اسم آهنگ"""
    chat_id = update.effective_chat.id
    if not context.args:
        await update.message.reply_text("❌ لطفا نام آهنگ را بعد از دستور /music وارد کنید.")
        return

    query = " ".join(context.args)
    msg = await update.message.reply_text(f"🔎 در حال جستجو برای: {query} ...")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
        "quiet": True,
        "noplaylist": True,
        "merge_output_format": "mp3"
    }

    search_query = f"ytsearch1:{query}"  # جستجوی یوتیوب و گرفتن اولین نتیجه

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=True)
            if not info:
                await msg.edit_text("❌ آهنگی پیدا نشد.")
                return

            # اسم فایل دانلود شده
            filename = ydl.prepare_filename(info if 'id' in info else info['entries'][0])
            mp3_path = await convert_to_mp3(filename)

            if mp3_path and os.path.exists(mp3_path):
                await context.bot.send_audio(chat_id, mp3_path, caption=f"🎵 {query}")
                os.remove(mp3_path)
            os.remove(filename)
            await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود آهنگ:\n{e}")

# ===============================
# اضافه کردن به ربات اصلی:
# application.add_handler(CommandHandler("music", music_handler))
