# modules/tiktok_handler.py
import os
import shutil
import subprocess
import requests
import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# -----------------------------
# تبدیل ویدیو به MP3 (Heroku Compatible)
# -----------------------------
async def convert_to_mp3(video_path: str) -> str:
    mp3_path = video_path.rsplit(".", 1)[0] + ".mp3"

    if not shutil.which("ffmpeg"):
        return None  # ffmpeg موجود نیست (مشکل از buildpack)

    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-ab", "192k", "-ar", "44100",
        "-f", "mp3", mp3_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return mp3_path


# -----------------------------
# هندلر تیک‌تاک
# -----------------------------
async def tiktok_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return  # پیام‌های غیرمتنی نادیده گرفته شود

    url = update.message.text.strip()

    # فقط لینک تیک‌تاک پذیرفته شود
    if "tiktok.com" not in url and "vm.tiktok.com" not in url and "vt.tiktok.com" not in url:
        return  # پیام‌های معمولی نادیده گرفته شود

    chat_id = update.effective_chat.id
    msg = await update.message.reply_text("⬇️ در حال پردازش TikTok ...")

    # -----------------------------
    # رفع لینک کوتاه TikTok
    # -----------------------------
    if "vm.tiktok.com" in url or "vt.tiktok.com" in url:
        try:
            resp = requests.get(url, allow_redirects=True)
            url = resp.url
        except Exception as e:
            await msg.edit_text(f"❌ خطا در ریدایرکت لینک: {e}")
            return

    # -----------------------------
    # جلوگیری از دانلود عکس‌ها
    # -----------------------------
    if "/photo/" in url:
        await msg.edit_text("❌ عکس‌های TikTok پشتیبانی نمی‌شوند.")
        return

    # -----------------------------
    # تنظیمات دانلود تیک‌تاک
    # -----------------------------
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

            if not info:
                await msg.edit_text("❌ ویدیو یافت نشد یا قابل دانلود نیست.")
                return

            filename = ydl.prepare_filename(info)

        # -----------------------------
        # ارسال ویدیو
        # -----------------------------
        await context.bot.send_video(chat_id, filename, caption=f"🎬 {info.get('title','TikTok Video')}")

        # -----------------------------
        # ارسال نسخه صوتی
        # -----------------------------
        mp3_path = await convert_to_mp3(filename)
        if mp3_path and os.path.exists(mp3_path):
            await context.bot.send_audio(chat_id, mp3_path, caption="🎵 نسخه صوتی ویدیو")
            os.remove(mp3_path)

        # پاک‌سازی فایل اصلی
        os.remove(filename)
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود: {e}")
