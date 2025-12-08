# modules/youtube_search_downloader.py

import os
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor

import yt_dlp
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler

# ================================
# سودو
# ================================
SUDO_USERS = [8588347189]

# ================================
# تنظیمات اولیه
# ================================
COOKIE_FILE = "modules/youtube_cookie.txt"
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

URL_RE = re.compile(r"(https?://[^\s]+)")
executor = ThreadPoolExecutor(max_workers=3)

# ذخیره لینک‌ها برای انتخاب کیفیت
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
        admin_ids = [a.user.id for a in admins]
        return user.id in admin_ids
    except:
        return False


# ================================
# دانلود با کیفیت سفارشی
# ================================
def _download_custom(url, fmt):
    ydl_opts = {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "format": fmt,
        "merge_output_format": "mp4",
        "noplaylist": True,
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as y:
        info = y.extract_info(url, download=True)
        filename = y.prepare_filename(info)
    return info, filename


# ================================
# هندلر اصلی — دریافت لینک
# ================================
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

    # محدودیت در گروه
    if update.effective_chat.type != "private":
        allowed = await is_admin(update, context)
        if not allowed:
            return  # سکوت کامل

    # ذخیره لینک
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
# مرحله ۲ — انتخاب کیفیت
# ================================
async def youtube_quality_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cq = update.callback_query
    chat_id = cq.message.chat_id
    await cq.answer()

    # محدودیت گروه
    allowed = await is_admin(update, context)
    if update.effective_chat.type != "private" and not allowed:
        return

    # دریافت لینک
    url = pending_links.get(chat_id)
    if not url:
        return await cq.edit_message_text("❌ لینک معتبر یافت نشد.")

    choice = cq.data

    # -----------------------------
    # AUDIO - دانلود فقط MP3
    # -----------------------------
    if choice == "yt_audio":

        await cq.edit_message_text("⬇ در حال دانلود صوت...")

        def audio_download():
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

        loop = asyncio.get_running_loop()
        info, file = await loop.run_in_executor(executor, audio_download)

        await context.bot.send_audio(chat_id, audio=open(file, "rb"), caption=f"🎵 {info.get('title')}")
        os.remove(file)
        return

    # -----------------------------
    # VIDEO - نمایش کیفیت‌ها
    # -----------------------------
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

    # -----------------------------
    # مرحله ۳ — دانلود با کیفیت انتخابی
    # -----------------------------
    if choice.startswith("v_"):

        quality = choice.split("_")[1] + "p"
        format_code = f"bestvideo[height<={quality[:-1]}]+bestaudio/best"

        await cq.edit_message_text(f"⬇ در حال دانلود کیفیت {quality} ...")

        loop = asyncio.get_running_loop()
        info, filename = await loop.run_in_executor(executor, _download_custom, url, format_code)

        await context.bot.send_video(
            chat_id, video=open(filename, "rb"), caption=f"🎬 {info.get('title')} ({quality})"
        )

        os.remove(filename)
        return
