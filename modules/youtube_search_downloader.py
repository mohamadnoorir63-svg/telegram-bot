# youtube_search_downloader.py — ULTRA TURBO v4 (Max Speed + 2GB Upload)

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
# INITIAL SETUP
# ====================================

COOKIE_FILE = "modules/youtube_cookie.txt"
os.makedirs("modules", exist_ok=True)

if not os.path.exists(COOKIE_FILE):
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        f.write("# Paste YouTube cookies here in Netscape format\n")

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

URL_RE = re.compile(r"(https?://[^\s]+)")

# 🚀 THREADPOOL — ULTRA TURBO 2025
executor = ThreadPoolExecutor(max_workers=40)

# Pending links for quality selection
pending_links = {}

# ====================================
# CHECK ADMIN
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
# ULTRA-TURBO VIDEO OPTIONS
# ====================================

def turbo_video_opts(max_height):
    return {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "ignoreerrors": True,
        "format": (
            f"bestvideo[height<={max_height}][ext=mp4]+bestaudio[ext=m4a]"
            f"/best[height<={max_height}]"
        ),
        "merge_output_format": "mp4",

        # ⚡ Ultra Turbo settings
        "concurrent_fragment_downloads": 64,
        "http_chunk_size": 4 * 1024 * 1024,
        "retries": 50,
        "fragment_retries": 50,
        "nopart": True,
        "noprogress": True,
        "overwrites": True,

        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.mp4",
    }

def turbo_audio_opts():
    return {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "ignoreerrors": True,
        "format": "bestaudio/best",

        "concurrent_fragment_downloads": 64,
        "http_chunk_size": 4 * 1024 * 1024,
        "retries": 50,
        "fragment_retries": 50,
        "nopart": True,
        "noprogress": True,
        "overwrites": True,

        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],

        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.mp3",
    }

# ====================================
# SYNC DOWNLOADERS
# ====================================

def _download_video_sync(url, max_height):
    opts = turbo_video_opts(max_height)
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)
        filename = y.prepare_filename(info)
    return info, filename


def _download_audio_sync(url):
    opts = turbo_audio_opts()
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)
        filename = y.prepare_filename(info)
    return info, filename

# ====================================
# STEP 1 — RECEIVE LINK
# ====================================

async def youtube_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    text = update.message.text.strip()
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
        "🎬 نوع دانلود را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ====================================
# STEP 2 & 3 — QUALITY SELECT + DOWNLOAD
# ====================================

async def youtube_quality_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    chat_id = cq.message.chat_id
    await cq.answer()

    # Only admins in groups
    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    url = pending_links.get(chat_id)

    if not url:
        return await cq.edit_message_text("❌ لینک معتبر یافت نشد.")

    choice = cq.data

    # --- AUDIO DOWNLOAD ---
    if choice == "yt_audio":
        await cq.edit_message_text("⬇ در حال دانلود صوت (Ultra Turbo)...")

        loop = asyncio.get_running_loop()
        info, audio_file = await loop.run_in_executor(
            executor, _download_audio_sync, url
        )

        await context.bot.send_document(
            chat_id,
            document=open(audio_file, "rb"),
            caption=f"🎵 {info.get('title', 'Audio')}",
        )

        await asyncio.sleep(3)
        os.remove(audio_file)
        return

    # --- VIDEO QUALITY MENU ---
    if choice == "yt_video":
        keyboard = [
            [InlineKeyboardButton("144p", callback_data="v_144")],
            [InlineKeyboardButton("240p", callback_data="v_240")],
            [InlineKeyboardButton("360p", callback_data="v_360")],
            [InlineKeyboardButton("480p", callback_data="v_480")],
            [InlineKeyboardButton("720p", callback_data="v_720")],
        ]

        return await cq.edit_message_text(
            "📺 کیفیت ویدیو را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # --- VIDEO DOWNLOAD ---
    if choice.startswith("v_"):
        q = int(choice.split("_")[1])

        await cq.edit_message_text(f"⬇ دانلود کیفیت {q}p (Ultra Turbo)...")

        loop = asyncio.get_running_loop()
        info, video_file = await loop.run_in_executor(
            executor, _download_video_sync, url, q
        )

        await context.bot.send_document(
            chat_id,
            document=open(video_file, "rb"),
            caption=f"🎬 {info.get('title', 'YouTube Video')} ({q}p)",
        )

        await asyncio.sleep(3)
        os.remove(video_file)
        return
