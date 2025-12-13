# youtube_search_downloader.py — ULTRA TURBO v5 (STABLE)

import os
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor

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
DOWNLOAD_FOLDER = "downloads"

os.makedirs("modules", exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

if not os.path.exists(COOKIE_FILE):
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        f.write("# Paste YouTube cookies here (Netscape format)\n")

URL_RE = re.compile(r"(https?://[^\s]+)")

# ====================================
# THREADPOOL
# ====================================

executor = ThreadPoolExecutor(max_workers=20)

pending_links = {}

# ====================================
# ADMIN CHECK
# ====================================

async def is_admin(update, context):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == "private":
        return True

    if user.id in SUDO_USERS:
        return True

    try:
        admins = await context.bot.get_chat_administrators(chat.id)
        return user.id in [a.user.id for a in admins]
    except:
        return False

# ====================================
# YTDLP OPTIONS
# ====================================

def turbo_video_opts(max_height):
    return {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "format": (
            f"bestvideo[height<={max_height}][ext=mp4]+bestaudio[ext=m4a]"
            f"/best[height<={max_height}]"
        ),
        "merge_output_format": "mp4",
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.mp4",

        # Stable Turbo
        "concurrent_fragment_downloads": 16,
        "http_chunk_size": 8 * 1024 * 1024,
        "retries": 20,
        "fragment_retries": 20,
        "nopart": True,
        "overwrites": True,
    }

def turbo_audio_opts():
    return {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "format": "bestaudio/best",
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",

        "concurrent_fragment_downloads": 16,
        "http_chunk_size": 8 * 1024 * 1024,
        "retries": 20,

        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

# ====================================
# SYNC DOWNLOAD
# ====================================

def _download_audio_sync(url):
    with yt_dlp.YoutubeDL(turbo_audio_opts()) as y:
        info = y.extract_info(url, download=True)
        audio_file = f"{DOWNLOAD_FOLDER}/{info['id']}.mp3"
    return info, audio_file

def _download_video_sync(url, q):
    with yt_dlp.YoutubeDL(turbo_video_opts(q)) as y:
        info = y.extract_info(url, download=True)
        video_file = f"{DOWNLOAD_FOLDER}/{info['id']}.mp4"
    return info, video_file

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
        [InlineKeyboardButton("🎬 Video (MP4)", callback_data="yt_video")],
    ]

    await update.message.reply_text(
        "⬇️ نوع دانلود را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ====================================
# STEP 2 — QUALITY & DOWNLOAD
# ====================================

async def youtube_quality_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()

    chat_id = cq.message.chat_id

    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    url = pending_links.get(chat_id)
    if not url:
        return await cq.edit_message_text("❌ لینک یافت نشد")

    loop = asyncio.get_running_loop()

    # AUDIO
    if cq.data == "yt_audio":
        await cq.edit_message_text("🎵 در حال دانلود صوت...")

        info, audio_file = await loop.run_in_executor(
            executor, _download_audio_sync, url
        )

        await context.bot.send_document(
            chat_id,
            document=open(audio_file, "rb"),
            caption=f"🎵 {info.get('title', '')}"
        )

        os.remove(audio_file)
        return

    # VIDEO MENU
    if cq.data == "yt_video":
        keyboard = [
            [InlineKeyboardButton("144p", callback_data="v_144")],
            [InlineKeyboardButton("240p", callback_data="v_240")],
            [InlineKeyboardButton("360p", callback_data="v_360")],
            [InlineKeyboardButton("480p", callback_data="v_480")],
            [InlineKeyboardButton("720p", callback_data="v_720")],
        ]

        return await cq.edit_message_text(
            "📺 کیفیت را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # VIDEO DOWNLOAD
    if cq.data.startswith("v_"):
        q = int(cq.data.split("_")[1])
        await cq.edit_message_text(f"🎬 دانلود {q}p ...")

        info, video_file = await loop.run_in_executor(
            executor, _download_video_sync, url, q
        )

        if os.path.getsize(video_file) > 1900 * 1024 * 1024:
            os.remove(video_file)
            return await context.bot.send_message(
                chat_id, "❌ حجم ویدیو بیشتر از حد مجاز تلگرام است"
            )

        await context.bot.send_document(
            chat_id,
            document=open(video_file, "rb"),
            caption=f"🎬 {info.get('title', '')} ({q}p)"
        )

        os.remove(video_file)
        return
