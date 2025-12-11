# Ultra Turbo v5 - YouTube Downloader with Cache + Multi-Download + Direct Stream
# FULL REWRITTEN VERSION

import os
import re
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

import yt_dlp
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# ====================================
# CONFIG
# ====================================

SUDO_USERS = [8588347189]

COOKIE_FILE = "modules/youtube_cookie.txt"
CACHE_FOLDER = "cache"
DOWNLOAD_FOLDER = "downloads"

MAX_CACHE_SIZE_MB = 5000
CACHE_EXPIRY = 7 * 24 * 3600  # 7 days

os.makedirs("modules", exist_ok=True)
os.makedirs(CACHE_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

if not os.path.exists(COOKIE_FILE):
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        f.write("# Paste YouTube cookies here in Netscape format\n")

URL_RE = re.compile(r"(https?://[^\s]+)")
executor = ThreadPoolExecutor(max_workers=40)

pending_links = {}
active_downloads = {}

# ====================================
# ADMIN CHECK
# ====================================

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
# CACHE SYSTEM
# ====================================

def clean_cache():
    files = sorted(
        ((f, os.path.getmtime(os.path.join(CACHE_FOLDER, f))) for f in os.listdir(CACHE_FOLDER)),
        key=lambda x: x[1]
    )

    total = sum(os.path.getsize(os.path.join(CACHE_FOLDER, f)) for f, _ in files)

    while total > MAX_CACHE_SIZE_MB * 1024 * 1024:
        old, _ = files.pop(0)
        try:
            os.remove(os.path.join(CACHE_FOLDER, old))
        except:
            pass

        total = sum(os.path.getsize(os.path.join(CACHE_FOLDER, f)) for f, _ in files)


def get_cached_file(video_id, ext):
    path = os.path.join(CACHE_FOLDER, f"{video_id}.{ext}")
    if os.path.exists(path):
        if time.time() - os.path.getmtime(path) > CACHE_EXPIRY:
            os.remove(path)
            return None
        return path
    return None


def save_to_cache(src, video_id, ext):
    dst = os.path.join(CACHE_FOLDER, f"{video_id}.{ext}")
    os.rename(src, dst)
    clean_cache()
    return dst

# ====================================
# YTDLP OPTIONS
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
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.mp3",
    }

# ====================================
# DIRECT STREAM (NO DOWNLOAD)
# ====================================

def get_direct_url(url, max_height):
    ydl_opts = {
        "quiet": True,
        "cookiefile": COOKIE_FILE,
        "skip_download": True,
        "format": f"best[height<={max_height}]",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as y:
        info = y.extract_info(url, download=False)
        return info["url"], info.get("title", "YouTube")

# ====================================
# SYNC DOWNLOAD FUNCTIONS
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
# STEP 1 – CATCH LINK
# ====================================

async def youtube():
    pass  # ادامه کد شما اینجا اضافه می‌شود
