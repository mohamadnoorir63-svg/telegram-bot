# modules/tiktok_handler.py

import os
import shutil
import subprocess
import requests
import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes

# ================================
# سودو
# ================================
SUDO_USERS = [8588347189]  # ← آیدی شما

# ================================
# فولدر دانلود
# ================================
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0 Safari/537.36"
)

# ================================
# چک مدیر بودن
# ================================
async def is_admin(update, context):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == "private":
        return True

    if user.id in SUDO_USERS:
        return True

    try:
        admins = await context.bot.get_chat_administrators(chat.id)
        admin_ids = [a.user.id for a in admins]
        return user.id in admin_ids
    except:
        return False


# ================================
# تبدیل به mp3
# ================================
async def convert_to_mp3(video_path: str) -> str:
    mp3_path = video_path.rsplit(".", 1)[0] + ".mp3"
    if not shutil.which("ffmpeg"):
        return None
    subprocess.run(
        ["ffmpeg", "-y", "-i", video_path, "-vn", "-ab", "192k", "-ar", "44100", mp3_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return mp3_path


# ================================
# هندلر اصلی TikTok
# ================================
async def tiktok_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    url = update.message.text.strip()

    if ("tiktok.com" not in url and 
        "vm.tiktok.com" not in url and 
        "vt.tiktok.com" not in url):
        return

    # محدودیت دسترسی در گروه (سکوت کامل برای کاربران عادی)
    if update.effective_chat.type != "private":
        allowed = await is_admin(update, context)
        if not allowed:
            return  # سکوت کامل

    msg = await update.message.reply_text("⬇️ در حال پردازش TikTok ...")
    chat_id = update.effective_chat.id

    # رفع ریدایرکت لینک کوتاه
    if "vm.tiktok.com" in url or "vt.tiktok.com" in url:
        try:
            resp = requests.get(url, allow_redirects=True, headers={"User-Agent": USER_AGENT})
            url = resp.url
        except Exception as e:
            await msg.edit_text(f"❌ خطا در ریدایرکت لینک: {e}")
            return

    if "/photo/" in url:
        await msg.edit_text("❌ عکس‌های TikTok پشتیبانی نمی‌شوند.")
        return

    # تنظیمات yt-dlp
    ydl_opts = {
        "quiet": True,
        "merge_output_format": "mp4",
        "noplaylist": True,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
        "format": "mp4",
        "http_headers": {
            "User-Agent": USER_AGENT,
            "Referer": "https://www.tiktok.com/"
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                await msg.edit_text("❌ ویدیو یافت نشد یا دانلود ممکن نیست.")
                return

            filename = ydl.prepare_filename(info)

        await context.bot.send_video(chat_id, filename, caption=f"🎬 {info.get('title', 'TikTok Video')}")

        # MP3
        mp3 = await convert_to_mp3(filename)
        if mp3 and os.path.exists(mp3):
            await context.bot.send_audio(chat_id, mp3, caption="🎵 نسخه صوتی")
            os.remove(mp3)

        os.remove(filename)
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود: {e}")
