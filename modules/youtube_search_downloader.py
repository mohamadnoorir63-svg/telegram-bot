import os
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

import yt_dlp
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# ====================================
# CONFIG
# ====================================
SUDO_USERS = [8588347189]
COOKIE_FILE = "modules/youtube_cookie.txt"
DOWNLOAD_FOLDER = "downloads"
MAX_FILE_SIZE = 800 * 1024 * 1024  # 800MB

os.makedirs("modules", exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

if not os.path.exists(COOKIE_FILE):
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        f.write("# Paste YouTube cookies here (Netscape format)\n")

URL_RE = re.compile(r"(https?://[^\s]+)")
executor = ThreadPoolExecutor(max_workers=6)
pending_links = {}  # chat_id: url

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
# YTDLP OPTIONS (ANTI-FREEZE)
# ====================================
def video_opts():
    return {
        "cookiefile": COOKIE_FILE,
        "quiet": True,

        # 🔥 کلید نجات: اصلاً فرمت سنگین انتخاب نمی‌شود
        "format": (
            "bestvideo[filesize_approx<=800M]/"
            "bestvideo[filesize<=800M]+"
            "bestaudio[filesize_approx<=100M]/"
            "best"
        ),

        "merge_output_format": "mp4",
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",

        # سبک برای سرور
        "concurrent_fragment_downloads": 4,
        "retries": 5,
        "fragment_retries": 5,

        "nopart": True,
        "overwrites": True,
        "ignoreerrors": False,
    }

def audio_opts():
    return {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "format": "bestaudio/best",
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "ignoreerrors": True,
    }

# ====================================
# SYNC DOWNLOAD
# ====================================
def _download_audio_sync(url):
    with yt_dlp.YoutubeDL(audio_opts()) as y:
        info = y.extract_info(url, download=True)
        return info, f"{DOWNLOAD_FOLDER}/{info['id']}.mp3"

def _download_video_sync(url):
    with yt_dlp.YoutubeDL(video_opts()) as y:
        info = y.extract_info(url, download=True)
        return info, f"{DOWNLOAD_FOLDER}/{info['id']}.mp4"

# ====================================
# CLEAN TEMP FILES
# ====================================
def cleanup_temp():
    for f in os.listdir(DOWNLOAD_FOLDER):
        path = os.path.join(DOWNLOAD_FOLDER, f)
        try:
            if os.path.isfile(path) and time.time() - os.path.getmtime(path) > 600:
                os.remove(path)
        except:
            pass

# ====================================
# STEP 1 — LINK
# ====================================
async def youtube_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    match = URL_RE.search(update.message.text)
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
# STEP 2 — DOWNLOAD
# ====================================
async def youtube_download_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cleanup_temp()
    cq = update.callback_query
    await cq.answer()
    chat_id = cq.message.chat.id

    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    url = pending_links.get(chat_id)
    if not url:
        return await cq.edit_message_text("❌ لینک یافت نشد")

    loop = asyncio.get_running_loop()

    # ---------- AUDIO ----------
    if cq.data == "yt_audio":
        await cq.edit_message_text("🎵 در حال دانلود صوت...")
        try:
            info, audio_file = await loop.run_in_executor(
                executor, _download_audio_sync, url
            )

            with open(audio_file, "rb") as f:
                await context.bot.send_document(
                    chat_id,
                    document=f,
                    caption=f"🎵 {info.get('title','')}"
                )
            os.remove(audio_file)
        except Exception as e:
            await context.bot.send_message(chat_id, f"❌ خطا\n{e}")

    # ---------- VIDEO ----------
    if cq.data == "yt_video":
        await cq.edit_message_text("🎬 در حال آماده‌سازی ویدیو...")

        try:
            info, video_file = await loop.run_in_executor(
                executor, _download_video_sync, url
            )

            with open(video_file, "rb") as f:
                await context.bot.send_video(
                    chat_id=chat_id,
                    video=f,
                    caption=f"🎬 {info.get('title','')}",
                    supports_streaming=True
                )

            os.remove(video_file)

        except Exception as e:
            await context.bot.send_message(
                chat_id,
                "❌ این ویدیو به دلیل محدودیت حجم قابل دانلود نیست\n"
                f"{e}"
            )
