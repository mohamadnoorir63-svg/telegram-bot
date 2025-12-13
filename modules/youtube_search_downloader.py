# youtube_search_downloader.py — ULTRA TURBO v7 (STREAM + AUTO BEST QUALITY)

import os
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
import subprocess

import yt_dlp
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# ====================================
# SUDO USERS
# ====================================
SUDO_USERS = [8588347189]

# ====================================
# PATHS
# ====================================
COOKIE_FILE = "modules/youtube_cookie.txt"
URL_RE = re.compile(r"(https?://[^\s]+)")
executor = ThreadPoolExecutor(max_workers=4)
pending_links = {}

MAX_FILE_SIZE = 1900 * 1024 * 1024  # حداکثر حجم تلگرام ~1.9GB

os.makedirs("modules", exist_ok=True)
if not os.path.exists(COOKIE_FILE):
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        f.write("# Paste YouTube cookies here (Netscape format)\n")

# ====================================
# ADMIN CHECK
# ====================================
async def is_admin(update, context):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private" or user.id in SUDO_USERS:
        return True
    try:
        admins = await context.bot.get_chat_administrators(chat.id)
        return user.id in [a.user.id for a in admins]
    except:
        return False

# ====================================
# STEP 1 — LINK
# ====================================
async def youtube_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    text = update.message.text
    match = URL_RE.search(text)
    if not match:
        return

    url = match.group(1)
    if "youtube.com" not in url and "youtu.be" not in url:
        return

    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    pending_links[update.effective_chat.id] = url

    keyboard = [
        [InlineKeyboardButton("🎵 Audio (MP3)", callback_data="yt_audio")],
        [InlineKeyboardButton("🎬 Video (MP4)", callback_data="yt_video")]
    ]

    await update.message.reply_text(
        "⬇️ نوع دانلود را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ====================================
# STEP 2 — STREAM DOWNLOAD
# ====================================
async def youtube_download_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    chat_id = cq.message.chat_id

    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    url = pending_links.get(chat_id)
    if not url:
        return await cq.edit_message_text("❌ لینک یافت نشد")

    await cq.edit_message_text("⬇️ در حال بررسی و پردازش...")

    loop = asyncio.get_running_loop()

    # اجرا در ThreadPool
    if cq.data == "yt_audio":
        await loop.run_in_executor(executor, stream_audio, url, context, chat_id)
    elif cq.data == "yt_video":
        await loop.run_in_executor(executor, stream_video, url, context, chat_id)

# ====================================
# STREAM AUDIO
# ====================================
def stream_audio(url, context, chat_id):
    ydl_opts = {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "format": "bestaudio/best",
        "noplaylist": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            filesize = info.get("filesize") or info.get("filesize_approx")
            if filesize and filesize > MAX_FILE_SIZE:
                asyncio.run_coroutine_threadsafe(
                    context.bot.send_message(
                        chat_id, "❌ حجم صوت بیشتر از حد مجاز تلگرام است."
                    ),
                    asyncio.get_event_loop()
                )
                return

            title = info.get("title", "Audio")
            process = subprocess.Popen(
                ["ffmpeg", "-i", url, "-f", "mp3", "pipe:1"],
                stdout=subprocess.PIPE
            )

            asyncio.run_coroutine_threadsafe(
                context.bot.send_audio(chat_id, audio=process.stdout, caption=f"🎵 {title}"),
                asyncio.get_event_loop()
            )
            process.stdout.close()
            process.wait()

    except Exception as e:
        asyncio.run_coroutine_threadsafe(
            context.bot.send_message(chat_id, f"❌ دانلود صوت ناموفق بود\n{e}"),
            asyncio.get_event_loop()
        )

# ====================================
# STREAM VIDEO
# ====================================
def stream_video(url, context, chat_id):
    ydl_opts = {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "format": "bestvideo+bestaudio/best",
        "noplaylist": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            # بررسی حجم ویدیو
            formats = info.get("formats", [])
            best_format = max(formats, key=lambda f: f.get("filesize") or 0)
            filesize = best_format.get("filesize") or best_format.get("filesize_approx")

            if filesize and filesize > MAX_FILE_SIZE:
                asyncio.run_coroutine_threadsafe(
                    context.bot.send_message(
                        chat_id, "❌ حجم ویدیو بیشتر از حد مجاز تلگرام است."
                    ),
                    asyncio.get_event_loop()
                )
                return

            title = info.get("title", "Video")
            process = subprocess.Popen(
                ["ffmpeg", "-i", url, "-f", "mp4", "pipe:1"],
                stdout=subprocess.PIPE
            )

            asyncio.run_coroutine_threadsafe(
                context.bot.send_video(chat_id, video=process.stdout, caption=f"🎬 {title}"),
                asyncio.get_event_loop()
            )
            process.stdout.close()
            process.wait()

    except Exception as e:
        asyncio.run_coroutine_threadsafe(
            context.bot.send_message(chat_id, f"❌ دانلود ویدیو ناموفق بود\n{e}"),
            asyncio.get_event_loop()
        )
