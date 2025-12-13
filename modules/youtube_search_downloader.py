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
MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB

os.makedirs("modules", exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

if not os.path.exists(COOKIE_FILE):
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        f.write("# Paste YouTube cookies here (Netscape format)\n")

URL_RE = re.compile(r"(https?://[^\s]+)")

executor = ThreadPoolExecutor(max_workers=30)
pending_links = {}  # chat_id: url
info_cache = {}     # url: info dict

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
def turbo_video_opts():
    return {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
        "concurrent_fragment_downloads": 32,
        "http_chunk_size": 8 * 1024 * 1024,
        "retries": 20,
        "fragment_retries": 20,
        "nopart": True,
        "overwrites": True,
        "ignoreerrors": True,
        "allow_unplayable_formats": True,
    }

def turbo_audio_opts():
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
    with yt_dlp.YoutubeDL(turbo_audio_opts()) as y:
        info = y.extract_info(url, download=True)
        if info is None or 'id' not in info:
            raise ValueError("❌ استخراج اطلاعات صوت ناموفق بود")
        audio_file = f"{DOWNLOAD_FOLDER}/{info['id']}.mp3"
        return info, audio_file

def _download_video_sync(url):
    with yt_dlp.YoutubeDL(turbo_video_opts()) as y:
        info = y.extract_info(url, download=True)
        if info is None or 'id' not in info:
            raise ValueError("❌ استخراج اطلاعات ویدیو ناموفق بود")
        video_file = f"{DOWNLOAD_FOLDER}/{info['id']}.mp4"
        return info, video_file

# ====================================
# CLEAN TEMP FILES
# ====================================
def cleanup_temp():
    for f in os.listdir(DOWNLOAD_FOLDER):
        file_path = os.path.join(DOWNLOAD_FOLDER, f)
        try:
            if os.path.isfile(file_path):
                if time.time() - os.path.getmtime(file_path) > 600:
                    os.remove(file_path)
        except Exception:
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
    # AUDIO → دانلود روی سرور
    # ------------------------
    if cq.data == "yt_audio":
        await cq.edit_message_text("🎵 در حال دانلود صوت (MP3)...")
        try:    
            info, audio_file = await loop.run_in_executor(executor, _download_audio_sync, url)    
        except Exception as e:    
            return await context.bot.send_message(chat_id, f"❌ دانلود یا ارسال صوت ناموفق بود\n{e}")    

        await context.bot.send_document(    
            chat_id,    
            document=open(audio_file, "rb"),    
            caption=f"🎵 {info.get('title', '')}"    
        )    
        os.remove(audio_file)    
        return

    # ------------------------
    # VIDEO → دانلود روی سرور با محدودیت حجم
    # ------------------------
    if cq.data == "yt_video":
        await cq.edit_message_text("🎬 در حال بررسی حجم ویدیو...")

        # بررسی حجم بدون دانلود کامل
        try:
            opts = {"quiet": True, "format": "bestvideo+bestaudio/best", "cookiefile": COOKIE_FILE}
            with yt_dlp.YoutubeDL(opts) as y:
                info = y.extract_info(url, download=False)
                info_cache[url] = info
                estimated_size = info.get('filesize') or info.get('filesize_approx') or 0
        except Exception as e:
            return await context.bot.send_message(chat_id, f"❌ دریافت اطلاعات ویدیو ناموفق بود\n{e}")

        if estimated_size > MAX_VIDEO_SIZE:
            return await cq.edit_message_text("❌ حجم ویدیو بیشتر از حد مجاز (500MB) است")

        # دانلود و ارسال
        await cq.edit_message_text("🎬 در حال دانلود ویدیو (بهترین کیفیت)...")
        try:
            info, video_file = await loop.run_in_executor(executor, _download_video_sync, url)
            await context.bot.send_video(
                chat_id=chat_id,
                video=open(video_file, "rb"),
                caption=f"🎬 {info.get('title','')}",
                supports_streaming=True
            )
            os.remove(video_file)
        except Exception as e:
            return await context.bot.send_message(chat_id, f"❌ دانلود یا ارسال ویدیو ناموفق بود\n{e}")
