# modules/youtube_search_downloader.py

import os
import re
import glob
import asyncio
import subprocess
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

os.makedirs("modules", exist_ok=True)
if not os.path.exists(COOKIE_FILE):
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        f.write("# Paste YouTube cookies here in Netscape format\n")

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

URL_RE = re.compile(r"(https?://[^\s]+)")

executor = ThreadPoolExecutor(max_workers=12)
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
# SUPER ULTRA TURBO OPTIONS
# ================================
def turbo_video_opts(max_height):
    return {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "ignoreerrors": True,
        "format": (
            f"bestvideo[height<={max_height}][ext=mp4]"
            f"+bestaudio[ext=m4a]/best[height<={max_height}]"
        ),
        "merge_output_format": "mp4",

        # Ultra Turbo Boost
        "concurrent_fragment_downloads": 50,
        "http_chunk_size": 5242880,
        "retries": 50,
        "fragment_retries": 50,
        "buffersize": 0,
        "ratelimit": 0,
        "throttled-rate": 0,
        "socket_timeout": 30,

        "nopart": True,
        "noprogress": True,
        "overwrites": True,

        # کیفیت نهایی کاملا استاندارد برای تلگرام
        "postprocessors": [
            {
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4"
            }
        ],

        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    }


def turbo_audio_opts():
    return {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "ignoreerrors": True,
        "format": "bestaudio/best",

        "concurrent_fragment_downloads": 50,
        "http_chunk_size": 5242880,
        "retries": 50,
        "fragment_retries": 50,

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
# پیدا کردن فایل خروجی نهایی
# ================================
def find_final_video_file(video_id):
    files = glob.glob(f"{DOWNLOAD_FOLDER}/{video_id}.*")
    files = [f for f in files if not f.endswith(".part")]

    if not files:
        return None

    for f in files:
        if f.endswith(".mp4"):
            return f

    return files[0]


# ================================
# تبدیل به MP4 استاندارد برای تلگرام
# ================================
def ensure_mp4(filepath):
    if filepath.endswith(".mp4"):
        return filepath

    new_path = filepath.rsplit(".", 1)[0] + ".mp4"

    subprocess.run([
        "ffmpeg", "-y",
        "-i", filepath,
        "-c:v", "libx264",
        "-c:a", "aac",
        new_path
    ])

    try:
        os.remove(filepath)
    except:
        pass

    return new_path


# ================================
# دانلود ویدیو (ULTRA TURBO + SAFE)
# ================================
def _download_video_sync(url, max_height):
    opts = turbo_video_opts(max_height)

    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)

    video_id = info.get("id")

    final_file = find_final_video_file(video_id)

    final_file = ensure_mp4(final_file)

    return info, final_file


# ================================
# دانلود صوت (ULTRA TURBO)
# ================================
def _download_audio_sync(url):
    opts = turbo_audio_opts()

    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)
        filename = y.prepare_filename(info)

    mp3 = filename.rsplit(".", 1)[0] + ".mp3"
    return info, mp3


# ================================
# مرحله ۱ — دریافت لینک و انتخاب نوع دانلود
# ================================
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
        "🎬 لطفاً نوع دانلود را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ================================
# مرحله ۲ و ۳ — انتخاب نوع و کیفیت
# ================================
async def youtube_quality_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

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

    # ------------------------------
    # AUDIO DL
    # ------------------------------
    if choice == "yt_audio":
        await cq.edit_message_text("⬇ در حال دانلود صوت (Ultra Turbo)...")

        loop = asyncio.get_running_loop()
        info, mp3_file = await loop.run_in_executor(
            executor, _download_audio_sync, url
        )

        await context.bot.send_audio(
            chat_id,
            audio=open(mp3_file, "rb"),
            caption=f"🎵 {info.get('title', 'Audio')}",
        )

        if os.path.exists(mp3_file):
            os.remove(mp3_file)
        return

    # ------------------------------
    # VIDEO MENU
    # ------------------------------
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
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # ------------------------------
    # VIDEO DOWNLOAD
    # ------------------------------
    if choice.startswith("v_"):
        q = int(choice.split("_")[1])
        quality_label = f"{q}p"

        await cq.edit_message_text(f"⬇ در حال دانلود کیفیت {quality_label} (Ultra Turbo)...")

        loop = asyncio.get_running_loop()
        info, video_file = await loop.run_in_executor(
            executor, _download_video_sync, url, q
        )

        await context.bot.send_video(
            chat_id,
            video=open(video_file, "rb"),
            caption=f"🎬 {info.get('title', 'YouTube Video')} ({quality_label})",
        )

        if os.path.exists(video_file):
            os.remove(video_file)
        return
