# modules/youtube_search_downloader.py

import os
import re
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

import yt_dlp
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# ====================
# سودو
# ====================
SUDO_USERS = [8588347189]

# ====================
# مسیرها
# ====================
COOKIE_FILE = "modules/youtube_cookie.txt"
DOWNLOAD_FOLDER = "downloads"
CACHE_FILE = "data/youtube_cache.json"

os.makedirs("modules", exist_ok=True)
os.makedirs("downloads", exist_ok=True)
os.makedirs("data", exist_ok=True)

# فایل کوکی اگر نیست
if not os.path.exists(COOKIE_FILE):
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        f.write("# paste cookies here")

# فایل کش اگر نیست
if not os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "w") as f:
        json.dump({}, f)

# بارگذاری کش
with open(CACHE_FILE, "r") as f:
    YT_CACHE = json.load(f)

URL_RE = re.compile(r"(https?://[^\s]+)")
executor = ThreadPoolExecutor(max_workers=3)
pending_links = {}


# ====================
# ذخیره‌سازی کش
# ====================
def save_cache():
    with open(CACHE_FILE, "w") as f:
        json.dump(YT_CACHE, f, indent=4)


# ====================
# استخراج video_id
# ====================
def extract_video_id(url):
    if "youtu.be/" in url:
        return url.split("/")[-1].split("?")[0]
    if "watch?v=" in url:
        return url.split("v=")[1].split("&")[0]
    return None


# ====================
# چک مدیر
# ====================
async def is_admin(update, context):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == "private":
        return True
    if user.id in SUDO_USERS:
        return True

    try:
        admins = await context.bot.get_chat_administrators(chat.id)
        admin_ids = [a.user.id for a in admins]
        return user.id in admin_ids
    except:
        return False


# ====================
# دانلود ویدیو
# ====================
def _download_video_sync(url, max_height=720):

    fmt = f"bestvideo[height<={max_height}]+bestaudio/best/best"

    ydl_opts = {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "format": fmt,
        "merge_output_format": "mp4",
        "noplaylist": True,
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    return info, filename


# ====================
# دانلود صوت
# ====================
def _download_audio_sync(url):

    ydl_opts = {
        "quiet": True,
        "cookiefile": COOKIE_FILE,
        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192"
        }],
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as y:
        info = y.extract_info(url, download=True)
        filename = y.prepare_filename(info)

    mp3 = filename.rsplit(".", 1)[0] + ".mp3"
    return info, mp3


# ====================
# مرحله ۱ → دریافت لینک
# ====================
async def youtube_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
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
        [InlineKeyboardButton("🎵 Audio", callback_data="yt_audio")],
        [InlineKeyboardButton("🎬 Video", callback_data="yt_video")],
    ]

    await update.message.reply_text(
        "🎬 لطفاً نوع دانلود را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ====================
# مرحله ۲ → انتخاب نوع
# ====================
async def youtube_quality_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cq = update.callback_query
    await cq.answer()

    chat_id = cq.message.chat_id
    url = pending_links.get(chat_id)
    if not url:
        return await cq.edit_message_text("❌ لینک معتبر یافت نشد.")

    video_id = extract_video_id(url)
    choice = cq.data

    # ------------------------------------
    # AUDIO
    # ------------------------------------
    if choice == "yt_audio":

        if video_id in YT_CACHE and "audio" in YT_CACHE[video_id]:
            file_id = YT_CACHE[video_id]["audio"]

            try:
                await cq.edit_message_text("⚡ ارسال سریع از کش...")
                return await context.bot.send_audio(chat_id, file_id)
            except:
                del YT_CACHE[video_id]["audio"]
                save_cache()

        await cq.edit_message_text("⬇ دانلود صوت...")

        loop = asyncio.get_running_loop()
        info, mp3_file = await loop.run_in_executor(executor, _download_audio_sync, url)

        msg = await context.bot.send_audio(
            chat_id,
            audio=open(mp3_file, "rb"),
            caption=f"🎵 {info.get('title')}"
        )

        if video_id not in YT_CACHE:
            YT_CACHE[video_id] = {}

        YT_CACHE[video_id]["audio"] = msg.audio.file_id
        save_cache()

        os.remove(mp3_file)
        return

    # ------------------------------------
    # VIDEO → انتخاب کیفیت
    # ------------------------------------
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

    # ------------------------------------
    # مرحله ۳ → دانلود کیفیت
    # ------------------------------------
    if choice.startswith("v_"):

        q = int(choice.split("_")[1])
        label = f"{q}p"
        key = f"video_{q}"

        # اگر در کش موجود است
        if video_id in YT_CACHE and key in YT_CACHE[video_id]:
            file_id = YT_CACHE[video_id][key]

            try:
                await cq.edit_message_text("⚡ ارسال سریع از کش...")
                return await context.bot.send_video(chat_id, file_id)
            except:
                del YT_CACHE[video_id][key]
                save_cache()

        await cq.edit_message_text(f"⬇ دانلود کیفیت {label} ...")

        loop = asyncio.get_running_loop()
        info, video_file = await loop.run_in_executor(
            executor, _download_video_sync, url, q
        )

        msg = await context.bot.send_video(
            chat_id,
            video=open(video_file, "rb"),
            caption=f"🎬 {info.get('title')} ({label})"
        )

        if video_id not in YT_CACHE:
            YT_CACHE[video_id] = {}

        YT_CACHE[video_id][key] = msg.video.file_id
        save_cache()

        os.remove(video_file)
        return
