import os
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
import yt_dlp

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

SUDO_USERS = [8588347189]

DOWNLOAD_FOLDER = "downloads"
CACHE_FOLDER = "downloads/youtube_cache"

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(CACHE_FOLDER, exist_ok=True)

telegram_cache = {}

URL_RE = re.compile(r"(https?://[^\s]+)")

executor = ThreadPoolExecutor(max_workers=5)   # 5 پایدارترین عدد


# ------------------------------------------------------
# یوتیوب در هروکو فقط با User-Agent پایدار کار می‌کند
# ------------------------------------------------------
YDL_BASE = {
    "quiet": True,
    "noprogress": True,
    "nocheckcertificate": True,
    "retries": 10,
    "fragment_retries": 10,
    "http_chunk_size": None,  # باعث گیر کردن نمی‌شود
    "user_agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}


# ------------------------------------------------------
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


# ------------------------------------------------------
def get_video_info(url):
    opts = YDL_BASE.copy()
    with yt_dlp.YoutubeDL(opts) as y:
        return y.extract_info(url, download=False)


# ------------------------------------------------------
def pick_best_height(info, max_height):
    formats = info.get("formats", [])
    heights = sorted({f.get("height") for f in formats if f.get("height")}, reverse=True)
    for h in heights:
        if h <= max_height:
            return h
    return heights[-1]


# ------------------------------------------------------
def download_audio(url, video_id):
    opts = YDL_BASE.copy()
    opts.update({
        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192"
        }],
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    })

    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)
        filename = y.prepare_filename(info)

    return info, filename.rsplit(".", 1)[0] + ".mp3"


# ------------------------------------------------------
def download_video(url, info, max_height):
    real_height = pick_best_height(info, max_height)

    fmt = f"bestvideo[height={real_height}]+bestaudio/best"

    opts = YDL_BASE.copy()
    opts.update({
        "format": fmt,
        "merge_output_format": "mp4",
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    })

    with yt_dlp.YoutubeDL(opts) as y:
        new_info = y.extract_info(url, download=True)
        filename = y.prepare_filename(new_info)

    return new_info, filename.rsplit(".", 1)[0] + ".mp4", real_height


# ------------------------------------------------------
pending_links = {}


async def youtube_search_handler(update: Update, context):

    if not update.message:
        return

    text = update.message.text
    print("YT CHECK:", text)  # DEBUG

    match = URL_RE.search(text)
    if not match:
        return

    url = match.group(1)

    if "youtube" not in url:
        return

    # اجازه
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


# ------------------------------------------------------
async def youtube_quality_handler(update: Update, context):

    cq = update.callback_query
    chat_id = cq.message.chat_id
    await cq.answer()

    url = pending_links.get(chat_id)
    if not url:
        return await cq.edit_message_text("❌ لینک پیدا نشد.")

    choice = cq.data

    # ========== AUDIO ==========
    if choice == "yt_audio":
        info = get_video_info(url)
        vid = info["id"]

        # کش
        if vid in telegram_cache and "mp3" in telegram_cache[vid]:
            return await context.bot.send_audio(
                chat_id,
                audio=telegram_cache[vid]["mp3"],
                caption=f"🎵 {info.get('title')}"
            )

        await cq.edit_message_text("⬇ در حال دانلود صوت...")

        loop = asyncio.get_running_loop()
        info, mp3 = await loop.run_in_executor(executor, download_audio, url, vid)

        msg = await context.bot.send_audio(chat_id, audio=open(mp3, "rb"),
                                           caption=f"🎵 {info.get('title')}")

        telegram_cache.setdefault(vid, {})["mp3"] = msg.audio.file_id
        return

    # ========== QUALITY CHOICE ==========
    if choice == "yt_video":
        keyboard = [
            [InlineKeyboardButton("144p", callback_data="v_144")],
            [InlineKeyboardButton("240p", callback_data="v_240")],
            [InlineKeyboardButton("360p", callback_data="v_360")],
            [InlineKeyboardButton("480p", callback_data="v_480")],
            [InlineKeyboardButton("720p", callback_data="v_720")],
        ]
        return await cq.edit_message_text("📺 کیفیت را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

    # ========== DOWNLOAD VIDEO ==========
    if choice.startswith("v_"):
        q = int(choice.split("_")[1])

        info = get_video_info(url)
        vid = info["id"]

        # کش تلگرام
        if vid in telegram_cache and str(q) in telegram_cache[vid]:
            return await context.bot.send_video(
                chat_id,
                video=telegram_cache[vid][str(q)],
                caption=f"🎬 {info.get('title')} ({q}p)"
            )

        await cq.edit_message_text(f"⬇ دانلود کیفیت {q}p ...")

        loop = asyncio.get_running_loop()
        info, mp4, height = await loop.run_in_executor(
            executor, download_video, url, info, q
        )

        msg = await context.bot.send_video(
            chat_id,
            video=open(mp4, "rb"),
            caption=f"🎬 {info.get('title')} ({height}p)"
        )

        telegram_cache.setdefault(vid, {})[str(q)] = msg.video.file_id
        return
