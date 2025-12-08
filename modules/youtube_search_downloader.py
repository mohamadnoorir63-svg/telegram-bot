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
SUDO_USERS = [8588347189]  # آیدی شما

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
executor = ThreadPoolExecutor(max_workers=3)

# ذخیره لینک‌ها برای انتخاب نوع و کیفیت
pending_links = {}


# ================================
# چک مدیر بودن
# ================================
async def is_admin(update, context):
    chat = update.effective_chat
    user = update.effective_user

    # پیوی → آزاد
    if chat.type == "private":
        return True

    # سودو → مجاز
    if user.id in SUDO_USERS:
        return True

    try:
        admins = await context.bot.get_chat_administrators(chat.id)
        admin_ids = [a.user.id for a in admins]
        return user.id in admin_ids
    except:
        return False


# ================================
# دانلود ویدیو با حداکثر ارتفاع سفارشی
# (فرمت بر اساس کد خودت، فقط height داینامیک شده)
# ================================
def _download_video_sync(url, max_height: int = 720):
    fmt = f"bestvideo[height<={max_height}]+bestaudio/best[height<={max_height}]/best"

    ydl_opts = {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "format": fmt,  # <- دقیقا با الگوی خودت، فقط height تغییر می‌کند
        "merge_output_format": "mp4",
        "noplaylist": True,
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    return info, filename


# ================================
# دانلود صوت (MP3)
# ================================
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


# ================================
# مرحله ۱ — دریافت لینک و نمایش پنل نوع دانلود
# ================================
async def youtube_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    # استخراج لینک
    match = URL_RE.search(text)
    if not match:
        return

    url = match.group(1)
    if "youtube.com" not in url and "youtu.be" not in url:
        return

    # محدودیت دسترسی در گروه
    if update.effective_chat.type != "private":
        allowed = await is_admin(update, context)
        if not allowed:
            return  # سکوت کامل

    # ذخیره لینک برای این چت
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
# مرحله ۲ و ۳ — انتخاب نوع و کیفیت
# ================================
async def youtube_quality_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cq = update.callback_query
    chat_id = cq.message.chat_id
    await cq.answer()

    # محدودیت دسترسی در گروه
    if update.effective_chat.type != "private":
        allowed = await is_admin(update, context)
        if not allowed:
            return  # سکوت کامل

    # لینک ذخیره‌شده
    url = pending_links.get(chat_id)
    if not url:
        return await cq.edit_message_text("❌ لینک معتبر یافت نشد.")

    choice = cq.data

    # -----------------------------
    # Audio — دانلود فقط صوت
    # -----------------------------
    if choice == "yt_audio":
        await cq.edit_message_text("⬇ در حال دانلود صوت...")

        loop = asyncio.get_running_loop()
        info, mp3_file = await loop.run_in_executor(
            executor, _download_audio_sync, url
        )

        await context.bot.send_audio(
            chat_id,
            audio=open(mp3_file, "rb"),
            caption=f"🎵 {info.get('title', 'Audio')}"
        )
        if os.path.exists(mp3_file):
            os.remove(mp3_file)
        return

    # -----------------------------
    # Video — نمایش گزینه کیفیت
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
    # کیفیت ویدیو — v_144 / v_240 / ...
    # -----------------------------
    if choice.startswith("v_"):

        # استخراج عدد کیفیت
        q = choice.split("_")[1]      # مثل "360"
        max_height = int(q)           # 360
        quality_label = f"{q}p"

        await cq.edit_message_text(f"⬇ در حال دانلود کیفیت {quality_label} ...")

        loop = asyncio.get_running_loop()
        info, video_file = await loop.run_in_executor(
            executor, _download_video_sync, url, max_height
        )

        await context.bot.send_video(
            chat_id,
            video=open(video_file, "rb"),
            caption=f"🎬 {info.get('title', 'YouTube Video')} ({quality_label})"
        )

        if os.path.exists(video_file):
            os.remove(video_file)
        return
