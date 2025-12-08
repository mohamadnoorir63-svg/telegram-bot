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
SUDO_USERS = [8588347189]

# ================================
# تنظیمات اولیه
# ================================

COOKIE_FILE = "modules/youtube_cookie.txt"
DOWNLOAD_FOLDER = "downloads"
CACHE_FOLDER = "downloads/youtube_cache"   # ← فولدر کش

os.makedirs("modules", exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(CACHE_FOLDER, exist_ok=True)

if not os.path.exists(COOKIE_FILE):
    with open(COOKIE_FILE, "w") as f:
        f.write("# Paste YouTube cookies here\n")

URL_RE = re.compile(r"(https?://[^\s]+)")

# 🔥 ThreadPool توربو
executor = ThreadPoolExecutor(max_workers=12)

# ذخیره لینک‌ها برای کیفیت
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
        return user.id in [a.user.id for a in admins]
    except:
        return False


# ================================
# سیستم کش
# ================================

def cache_get(video_id, ext):
    """اگر کش موجود باشد، مسیر فایل را برمی‌گرداند"""
    path = os.path.join(CACHE_FOLDER, f"{video_id}.{ext}")
    return path if os.path.exists(path) else None


def cache_save(src_path, video_id, ext):
    """فایل دانلودشده را در کش ذخیره می‌کند"""
    dst_path = os.path.join(CACHE_FOLDER, f"{video_id}.{ext}")
    if os.path.exists(dst_path):
        return dst_path
    try:
        os.rename(src_path, dst_path)
    except:
        pass
    return dst_path


# ================================
# Turbo Options for yt-dlp
# ================================

def turbo_video_opts(max_height):
    return {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "ignoreerrors": True,
        "format": f"bestvideo[height<={max_height}]+bestaudio/best/best",
        "merge_output_format": "mp4",

        "concurrent_fragment_downloads": 20,
        "http_chunk_size": 1048576,
        "fragment_retries": 25,
        "retries": 25,
        "nopart": True,
        "noprogress": True,
        "overwrites": True,

        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    }


def turbo_audio_opts():
    return {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "ignoreerrors": True,
        "format": "bestaudio/best",

        "concurrent_fragment_downloads": 20,
        "http_chunk_size": 1048576,
        "fragment_retries": 25,
        "retries": 25,

        "nopart": True,
        "noprogress": True,
        "overwrites": True,

        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192"
        }],

        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    }


# ================================
# دانلود صوت (Turbo + Cache)
# ================================
def _download_audio_sync(url):

    # مرحله ۱: اول چک کنیم کش دارد؟
    with yt_dlp.YoutubeDL({"quiet": True}) as y:
        info = y.extract_info(url, download=False)
        video_id = info["id"]

    cached = cache_get(video_id, "mp3")
    if cached:
        return info, cached

    # مرحله ۲: دانلود
    opts = turbo_audio_opts()

    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)
        filename = y.prepare_filename(info)

    mp3 = filename.rsplit(".", 1)[0] + ".mp3"

    # مرحله ۳: ذخیره در کش
    final_path = cache_save(mp3, info["id"], "mp3")

    return info, final_path


# ================================
# دانلود ویدیو (Turbo + Cache)
# ================================
def _download_video_sync(url, max_height):

    # مرحله ۱: چک کش
    with yt_dlp.YoutubeDL({"quiet": True}) as y:
        info = y.extract_info(url, download=False)
        video_id = info["id"]

    cached = cache_get(video_id, "mp4")
    if cached:
        return info, cached

    # مرحله ۲: دانلود جدید
    opts = turbo_video_opts(max_height)

    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)
        filename = y.prepare_filename(info)

    mp4 = filename.rsplit(".", 1)[0] + ".mp4"

    # مرحله ۳: ذخیره در کش
    final_path = cache_save(mp4, info["id"], "mp4")

    return info, final_path


# ================================
# مرحله ۱ — دریافت لینک
# ================================
async def youtube_search_handler(update: Update, context):

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
        "🎬 لطفاً نوع دانلود را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================================
# مرحله ۲ و ۳ — Audio/Video + کیفیت‌ها
# ================================
async def youtube_quality_handler(update: Update, context):

    cq = update.callback_query
    chat_id = cq.message.chat_id
    await cq.answer()

    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    url = pending_links.get(chat_id)
    if not url:
        return await cq.edit_message_text("❌ لینک معتبر یافت نشد.")

    choice = cq.data

    # -----------------------
    # Audio (MP3)
    # -----------------------
    if choice == "yt_audio":
        await cq.edit_message_text("⬇ در حال دانلود صوت (Turbo + Cache)...")

        loop = asyncio.get_running_loop()
        info, mp3 = await loop.run_in_executor(
            executor, _download_audio_sync, url
        )

        await context.bot.send_audio(
            chat_id,
            audio=open(mp3, "rb"),
            caption=f"🎵 {info.get('title', 'Audio')}"
        )
        return

    # -----------------------
    # Video Menu
    # -----------------------
    if choice == "yt_video":
        keyboard = [
            [InlineKeyboardButton("144p", callback_data="v_144")],
            [InlineKeyboardButton("240p", callback_data="v_240")],
            [InlineKeyboardButton("360p", callback_data="v_360")],
            [InlineKeyboardButton("480p", callback_data="v_480")],
            [InlineKeyboardButton("720p", callback_data="v_720")],
        ]
        return await cq.edit_message_text(
            "📺 لطفاً کیفیت ویدیو را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # -----------------------
    # Video Download
    # -----------------------
    if choice.startswith("v_"):
        q = int(choice.split("_")[1])
        await cq.edit_message_text(f"⬇ در حال دانلود کیفیت {q}p (Turbo + Cache)...")

        loop = asyncio.get_running_loop()
        info, mp4 = await loop.run_in_executor(
            executor, _download_video_sync, url, q
        )

        await context.bot.send_video(
            chat_id,
            video=open(mp4, "rb"),
            caption=f"🎬 {info.get('title', 'YouTube Video')} ({q}p)"
        )
        return
