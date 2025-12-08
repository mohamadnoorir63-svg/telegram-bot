# modules/youtube_search_downloader.py

import os
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor

import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes

# ================================
# سودو
# ================================
SUDO_USERS = [8588347189]  # آیدی شما

# ================================
# تنظیمات اولیه
# ================================
COOKIE_FILE = "modules/youtube_cookie.txt"

os.makedirs("modules", exist_ok=True)
if not os.path.exists(COOKIE_FILE):
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        f.write("# Paste YouTube cookies here in Netscape format\n")

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

URL_RE = re.compile(r"(https?://[^\s]+)")
executor = ThreadPoolExecutor(max_workers=3)


# ================================
# چک مدیر بودن
# ================================
async def is_admin(update, context):
    chat = update.effective_chat
    user = update.effective_user

    # پیوی → آزاد
    if chat.type == "private":
        return True

    # سودو → مجاز
    if user.id in SUDO_USERS:
        return True

    try:
        admins = await context.bot.get_chat_administrators(chat.id)
        admin_ids = [a.user.id for a in admins]
        return user.id in admin_ids
    except:
        return False


# ================================
# دانلود ویدیو
# ================================
def _download_video_sync(url):
    ydl_opts = {
        "cookiefile": COOKIE_FILE,
        "quiet": True,

        # کیفیت استاندارد و بدون مشکل EJS
        "format": "bestvideo[height<=720]+bestaudio/best[height<=720]/best",

        "merge_output_format": "mp4",
        "noplaylist": True,
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    return info, filename


# ================================
# هندلر اصلی — دانلود یوتیوب
# ================================
async def youtube_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    # استخراج لینک
    match = URL_RE.search(text)
    if not match:
        return

    url = match.group(1)
    if "youtube.com" not in url and "youtu.be" not in url:
        return

    # محدودیت دسترسی در گروه
    if update.effective_chat.type != "private":
        allowed = await is_admin(update, context)
        if not allowed:
            return  # سکوت کامل

    msg = await update.message.reply_text("📥 در حال دانلود ویدیو... لطفاً صبر کنید.")

    loop = asyncio.get_running_loop()
    try:
        info, video_file = await loop.run_in_executor(
            executor, _download_video_sync, url
        )
    except Exception as e:
        return await msg.edit_text(f"❌ خطا در دانلود:\n{e}")

    title = info.get("title", "YouTube Video")

    await msg.edit_text("⬇ در حال ارسال ویدیو...")

    try:
        await update.message.reply_video(
            video=open(video_file, "rb"),
            caption=f"🎬 {title}"
        )
    except Exception as e:
        await msg.edit_text(f"❌ خطا در ارسال ویدیو:\n{e}")
    finally:
        if os.path.exists(video_file):
            os.remove(video_file)
