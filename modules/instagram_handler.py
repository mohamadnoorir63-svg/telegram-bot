# modules/instagram_handler.py
import os
import shutil
import subprocess
import requests
import yt_dlp
import uuid
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
    """دانلود ویدیوهای Instagram با session جدید برای هر لینک"""
    if not update.message or not update.message.text:
        return

    url = update.message.text.strip()
    chat_id = update.effective_chat.id

    # فقط لینک‌های اینستاگرام
    if "instagram.com" not in url:
        return

    msg = await update.message.reply_text("⬇️ در حال دانلود از Instagram ...")

    # بررسی عکس‌ها
    if "/p/" in url and not any(x in url for x in ["/reel/", "/tv/"]):
        await msg.edit_text("❌ این لینک عکس است و پشتیبانی نمی‌شود.")
        return

    # ریدایرکت لینک کوتاه
    try:
        resp = requests.get(url, allow_redirects=True)
        url = resp.url
    except:
        pass

    # هر بار یک session جدید و مسیر یکتا برای فایل
    outtmpl = os.path.join(DOWNLOAD_FOLDER, f"%(id)s_{uuid.uuid4().hex}.%(ext)s")
    ydl_opts = {
        "quiet": True,
        "format": "best",
        "outtmpl": outtmpl,
        "noplaylist": False,
        "merge_output_format": "mp4",
        "ignoreerrors": True,
        "extract_flat": False,
        "cachedir": False,
        "nocheckcertificate": True,      # گاهی certificate مشکل ایجاد می‌کنه
        "noprogress": True,
        "restrictfilenames": True,       # جلوگیری از کاراکترهای عجیب در نام فایل
        "force_generic_extractor": True, # استفاده از generic extractor برای session جدید
    }

    try:
        # هر بار یک instance جدا از YoutubeDL
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        if not info:
            await msg.edit_text("❌ امکان دانلود این پست وجود ندارد.")
            return

        # چند ویدیو (Carousel)
        entries = info.get("entries")
        if entries:
            for item in entries:
                filename = ydl.prepare_filename(item)
                if os.path.exists(filename):
                    await context.bot.send_video(chat_id, filename, caption=f"🎬 {item.get('title', 'Instagram Video')}")
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
        await msg.edit_text(f"❌ خطا در دانلود از اینستاگرام:\n{e}")
