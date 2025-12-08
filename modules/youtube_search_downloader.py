import os
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
import yt_dlp

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes


# ============================
# سودو
# ============================
SUDO_USERS = [8588347189]

# ============================
# پوشه‌ها
# ============================
DOWNLOAD_FOLDER = "downloads"
CACHE_FOLDER = "downloads/youtube_cache"

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(CACHE_FOLDER, exist_ok=True)

# کش فایل‌های تلگرام
telegram_cache = {}   # {video_id: {"mp3": file_id, "720": file_id, ...}}

URL_RE = re.compile(r"(https?://[^\s]+)")

executor = ThreadPoolExecutor(max_workers=12)


# ============================
# چک ادمین
# ============================
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


# ============================
# گرفتن video_id بدون دانلود
# ============================
def get_video_info(url):
    with yt_dlp.YoutubeDL({"quiet": True}) as y:
        return y.extract_info(url, download=False)


# ============================
# پیدا کردن نزدیک‌ترین کیفیت
# ============================
def pick_best_height(info, max_height):
    formats = info.get("formats", [])
    heights = sorted({f.get("height") for f in formats if f.get("height")}, reverse=True)

    for h in heights:
        if h <= max_height:
            return h
    return heights[-1]  # پایین‌ترین کیفیت موجود


# ============================
# دانلود MP3 (Turbo)
# ============================
def download_audio(url, video_id):

    opts = {
        "quiet": True,
        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192"
        }],
        "concurrent_fragment_downloads": 20,
        "http_chunk_size": 1048576,
        "noprogress": True,
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    }

    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)
        filename = y.prepare_filename(info)

    return info, filename.rsplit(".", 1)[0] + ".mp3"


# ============================
# دانلود ویدیو (Turbo)
# ============================
def download_video(url, info, max_height):

    real_height = pick_best_height(info, max_height)

    fmt = f"bestvideo[height={real_height}]+bestaudio/best"

    opts = {
        "quiet": True,
        "format": fmt,
        "merge_output_format": "mp4",
        "concurrent_fragment_downloads": 20,
        "http_chunk_size": 1048576,
        "noprogress": True,
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    }

    with yt_dlp.YoutubeDL(opts) as y:
        new_info = y.extract_info(url, download=True)
        filename = y.prepare_filename(new_info)

    return new_info, filename.rsplit(".", 1)[0] + ".mp4", real_height


# ============================
# مرحله ۱ — گرفتن لینک
# ============================
pending_links = {}

async def youtube_search_handler(update: Update, context):

    if not update.message:
        return

    text = update.message.text
    match = URL_RE.search(text)
    if not match:
        return

    url = match.group(1)

    if "youtube" not in url:
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


# ============================
# مرحله ۲ — Audio / Video انتخاب
# ============================
async def youtube_quality_handler(update: Update, context):

    cq = update.callback_query
    chat_id = cq.message.chat_id
    await cq.answer()

    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    url = pending_links.get(chat_id)
    if not url:
        return await cq.edit_message_text("❌ لینک پیدا نشد.")

    choice = cq.data

    # =======================
    # صوت (MP3)
    # =======================
    if choice == "yt_audio":
        info = get_video_info(url)
        vid = info["id"]

        # 🔥 کش تلگرام
        if vid in telegram_cache and "mp3" in telegram_cache[vid]:
            file_id = telegram_cache[vid]["mp3"]
            return await context.bot.send_audio(
                chat_id,
                audio=file_id,
                caption=f"🎵 {info.get('title')}"
            )

        await cq.edit_message_text("⬇ در حال دانلود صوت...")

        loop = asyncio.get_running_loop()
        info, mp3 = await loop.run_in_executor(executor, download_audio, url, vid)

        msg = await context.bot.send_audio(
            chat_id,
            audio=open(mp3, "rb"),
            caption=f"🎵 {info.get('title')}"
        )

        # ذخیره file_id
        telegram_cache.setdefault(vid, {})["mp3"] = msg.audio.file_id

        return

    # =======================
    # نمایش کیفیت ویدیو
    # =======================
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

    # =======================
    # دانلود ویدیو + کش تلگرام
    # =======================
    if choice.startswith("v_"):

        q = int(choice.split("_")[1])
        info = get_video_info(url)
        vid = info["id"]

        # 🔥 اگر همین کیفیت قبلاً ارسال شده → فوری بفرست
        if vid in telegram_cache and str(q) in telegram_cache[vid]:
            file_id = telegram_cache[vid][str(q)]
            return await context.bot.send_video(
                chat_id,
                video=file_id,
                caption=f"🎬 {info.get('title')} ({q}p)"
            )

        await cq.edit_message_text(f"⬇ دانلود کیفیت {q}p ...")

        loop = asyncio.get_running_loop()
        info, mp4, real_height = await loop.run_in_executor(
            executor, download_video, url, info, q
        )

        msg = await context.bot.send_video(
            chat_id,
            video=open(mp4, "rb"),
            caption=f"🎬 {info.get('title')} ({real_height}p)"
        )

        # ذخیره file_id
        telegram_cache.setdefault(vid, {})[str(q)] = msg.video.file_id

        return
