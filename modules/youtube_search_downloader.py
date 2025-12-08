# modules/youtube_search_downloader.py

import os
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor

import yt_dlp
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
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

# لینک‌های ذخیره شده برای انتخاب صوت/تصویر
pending_links = {}


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
# دانلود ویدیو (کد **دقیقاً همان** کد خودت)
# ================================
def _download_video_sync(url):
    ydl_opts = {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
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
# دانلود صوت
# ================================
def _download_audio_sync(url):
    ydl_opts = {
        "quiet": True,
        "cookiefile": COOKIE_FILE,

        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192"
        }],

        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as y:
        info = y.extract_info(url, download=True)
        filename = y.prepare_filename(info)

    mp3 = filename.rsplit(".", 1)[0] + ".mp3"
    return info, mp3


# ================================
# مرحله 1 → دریافت لینک فقط پنل بده
# ================================
async def youtube_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    match = URL_RE.search(text)
    if not match:
        return

    url = match.group(1)

    if "youtube.com" not in url and "youtu.be" not in url:
        return

    # محدودیت گروه
    if update.effective_chat.type != "private":
        allowed = await is_admin(update, context)
        if not allowed:
            return  # سکوت کامل

    # ذخیره لینک
    pending_links[update.effective_chat.id] = url

    keyboard = [
        [InlineKeyboardButton("🎵 دانلود صوتی (MP3)", callback_data="yt_audio")],
        [InlineKeyboardButton("🎬 دانلود تصویری (720p)", callback_data="yt_video")],
    ]

    await update.message.reply_text(
        "🎬 لطفاً نوع دانلود را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================================
# مرحله 2 → انتخاب صوتی یا تصویری
# ================================
async def youtube_choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cq = update.callback_query
    await cq.answer()

    chat_id = cq.message.chat_id

    # محدودیت گروه
    allowed = await is_admin(update, context)
    if update.effective_chat.type != "private" and not allowed:
        return

    # گرفتن لینک
    url = pending_links.get(chat_id)
    if not url:
        return await cq.edit_message_text("❌ لینک معتبر یافت نشد.")

    choice = cq.data

    # ------------------------
    # صوتی (MP3)
    # ------------------------
    if choice == "yt_audio":
        await cq.edit_message_text("⬇ در حال دانلود صوت ...")

        loop = asyncio.get_running_loop()
        info, mp3_file = await loop.run_in_executor(executor, _download_audio_sync, url)

        await context.bot.send_audio(chat_id, open(mp3_file, "rb"), caption=f"🎵 {info.get('title')}")
        os.remove(mp3_file)
        return

    # ------------------------
    # تصویری (همان کیفیت خودت)
    # ------------------------
    if choice == "yt_video":
        await cq.edit_message_text("⬇ در حال دانلود ویدیو (720p)...")

        loop = asyncio.get_running_loop()
        info, video_file = await loop.run_in_executor(executor, _download_video_sync, url)

        await context.bot.send_video(
            chat_id,
            open(video_file, "rb"),
            caption=f"🎬 {info.get('title')} (720p)"
        )

        os.remove(video_file)
        return
