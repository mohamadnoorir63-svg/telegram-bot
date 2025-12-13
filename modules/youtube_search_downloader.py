import os
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor

import yt_dlp
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import ContextTypes

# ====================================
# CONFIG
# ====================================

SUDO_USERS = [8588347189]

COOKIE_FILE = "modules/youtube_cookie.txt"
DOWNLOAD_FOLDER = "downloads"

os.makedirs("modules", exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

if not os.path.exists(COOKIE_FILE):
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        f.write("# YouTube cookies (Netscape format)\n")

URL_RE = re.compile(r"(https?://[^\s]+)")

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
# YT-DLP OPTIONS (2025 SAFE)
# ====================================

COMMON_EXTRACTOR_ARGS = {
    "youtube": {
        "player_client": ["android", "web"],
        "skip": ["dash"],
    }
}

def video_opts(max_height):
    return {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "ignoreerrors": True,

        "format": (
            f"bestvideo[height<={max_height}][ext=mp4]+bestaudio[ext=m4a]"
            f"/best[height<={max_height}]"
        ),
        "merge_output_format": "mp4",
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.mp4",

        "concurrent_fragment_downloads": 16,
        "http_chunk_size": 8 * 1024 * 1024,
        "retries": 20,
        "fragment_retries": 20,
        "nopart": True,
        "overwrites": True,

        "extractor_args": COMMON_EXTRACTOR_ARGS,
    }

def audio_opts():
    return {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "ignoreerrors": True,

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

        "extractor_args": COMMON_EXTRACTOR_ARGS,
    }

# ====================================
# DOWNLOADERS (SYNC)
# ====================================

def download_audio(url):
    with yt_dlp.YoutubeDL(audio_opts()) as y:
        info = y.extract_info(url, download=True)
        path = f"{DOWNLOAD_FOLDER}/{info['id']}.mp3"
    return info, path

def download_video(url, q):
    with yt_dlp.YoutubeDL(video_opts(q)) as y:
        info = y.extract_info(url, download=True)
        path = f"{DOWNLOAD_FOLDER}/{info['id']}.mp4"
    return info, path

# ====================================
# STEP 1 — LINK
# ====================================

async def youtube_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    text = update.message.text
    m = URL_RE.search(text)
    if not m:
        return

    url = m.group(1)
    if "youtube.com" not in url and "youtu.be" not in url:
        return

    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    pending_links[update.effective_chat.id] = url

    await update.message.reply_text(
        "⬇️ نوع دانلود را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎵 Audio (MP3)", callback_data="yt_audio")],
            [InlineKeyboardButton("🎬 Video (MP4)", callback_data="yt_video")],
        ])
    )

# ====================================
# STEP 2 — CALLBACK (SAFE)
# ====================================

async def youtube_quality_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    chat_id = cq.message.chat_id

    # پاسخ سریع (حل Query too old)
    try:
        await cq.answer("⏳ پردازش...", show_alert=False)
    except:
        pass

    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    url = pending_links.get(chat_id)
    if not url:
        return await cq.edit_message_text("❌ لینک منقضی شده است")

    loop = asyncio.get_running_loop()

    # ===== AUDIO =====
    if cq.data == "yt_audio":
        await cq.edit_message_text("🎵 دانلود صوت شروع شد...")

        info, path = await loop.run_in_executor(
            executor, download_audio, url
        )

        await context.bot.send_document(
            chat_id,
            document=open(path, "rb"),
            caption=f"🎵 {info.get('title','')}"
        )

        os.remove(path)
        return

    # ===== VIDEO MENU =====
    if cq.data == "yt_video":
        return await cq.edit_message_text(
            "📺 کیفیت را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("144p", callback_data="v_144")],
                [InlineKeyboardButton("240p", callback_data="v_240")],
                [InlineKeyboardButton("360p", callback_data="v_360")],
                [InlineKeyboardButton("480p", callback_data="v_480")],
                [InlineKeyboardButton("720p", callback_data="v_720")],
            ])
        )

    # ===== VIDEO DOWNLOAD =====
    if cq.data.startswith("v_"):
        q = int(cq.data.split("_")[1])
        await cq.edit_message_text(f"🎬 دانلود {q}p شروع شد...")

        info, path = await loop.run_in_executor(
            executor, download_video, url, q
        )

        if os.path.getsize(path) > 1900 * 1024 * 1024:
            os.remove(path)
            return await context.bot.send_message(
                chat_id, "❌ حجم ویدیو بیش از محدودیت تلگرام است"
            )

        await context.bot.send_document(
            chat_id,
            document=open(path, "rb"),
            caption=f"🎬 {info.get('title','')} ({q}p)"
        )

        os.remove(path)
        return
