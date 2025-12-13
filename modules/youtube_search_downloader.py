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

executor = ThreadPoolExecutor(max_workers=20)
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
# YTDLP OPTIONS
# ====================================
def audio_opts():
    return {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "format": "bestaudio/best",
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
        "concurrent_fragment_downloads": 32,
        "http_chunk_size": 8 * 1024 * 1024,
        "retries": 20,
        "fragment_retries": 20,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "ignoreerrors": True,
        "allow_unplayable_formats": True,
    }

# ====================================
# SYNC DOWNLOAD
# ====================================
def _download_audio_sync(url):
    with yt_dlp.YoutubeDL(audio_opts()) as y:
        info = y.extract_info(url, download=True)
        if info is None or 'id' not in info:
            raise ValueError("❌ استخراج اطلاعات صوت ناموفق بود")
        audio_file = f"{DOWNLOAD_FOLDER}/{info['id']}.mp3"
        return info, audio_file

# ====================================
# CLEAN TEMP FILES
# ====================================
def cleanup_temp():
    for f in os.listdir(DOWNLOAD_FOLDER):
        file_path = os.path.join(DOWNLOAD_FOLDER, f)
        try:
            if os.path.isfile(file_path) and time.time() - os.path.getmtime(file_path) > 600:
                os.remove(file_path)
        except:
            pass

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
# STEP 2 — DOWNLOAD / SEND (HYBRID)
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

    # ------------------------
    # AUDIO → دانلود روی سرور خودت
    # ------------------------
    if cq.data == "yt_audio":
        await cq.edit_message_text("🎵 در حال دانلود صوت (MP3)...")
        try:
            info, audio_file = await loop.run_in_executor(executor, _download_audio_sync, url)
        except Exception as e:
            return await context.bot.send_message(chat_id, f"❌ دانلود یا ارسال صوت ناموفق بود\n{e}")

        size = os.path.getsize(audio_file)
        if size > MAX_FILE_SIZE:
            os.remove(audio_file)
            return await cq.edit_message_text("❌ حجم فایل صوتی بیشتر از حد مجاز (800MB) است")

        await context.bot.send_document(
            chat_id,
            document=open(audio_file, "rb"),
            caption=f"🎵 {info.get('title', '')}"
        )
        os.remove(audio_file)
        return

    # ------------------------
    # VIDEO → مستقیم روی سرور تلگرام
    # ------------------------
    if cq.data == "yt_video":
        await cq.edit_message_text("🎬 در حال بررسی حجم ویدیو...")

        try:
            opts = {"quiet": True, "format": "bestvideo+bestaudio/best", "cookiefile": COOKIE_FILE}
            with yt_dlp.YoutubeDL(opts) as y:
                info = y.extract_info(url, download=False)
                # پیدا کردن بهترین فرمت ترکیبی video+audio
                formats = sorted(info.get('formats', []), key=lambda x: x.get('filesize') or x.get('filesize_approx') or 0, reverse=True)
                direct_url = None
                estimated_size = 0
                for f in formats:
                    if f.get('acodec') != 'none' and f.get('vcodec') != 'none':
                        direct_url = f.get('url')
                        estimated_size = f.get('filesize') or f.get('filesize_approx') or 0
                        break

                if direct_url is None:
                    return await cq.edit_message_text("❌ ویدیو قابل پخش مستقیم یافت نشد")

        except Exception as e:
            return await context.bot.send_message(chat_id, f"❌ دریافت اطلاعات ویدیو ناموفق بود\n{e}")

        if estimated_size > MAX_FILE_SIZE:
            return await cq.edit_message_text("❌ حجم ویدیو بیشتر از حد مجاز (800MB) است")

        await cq.edit_message_text("🎬 در حال ارسال ویدیو مستقیم روی تلگرام...")
        try:
            await context.bot.send_video(
                chat_id=chat_id,
                video=direct_url,
                caption=f"🎬 {info.get('title', '')}",
                supports_streaming=True
            )
        except Exception as e:
            return await context.bot.send_message(chat_id, f"❌ ارسال ویدیو مستقیم ناموفق بود\n{e}")
