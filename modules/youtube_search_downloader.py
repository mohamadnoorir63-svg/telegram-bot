# modules/youtube_search_downloader.py

import os
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json

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
DOWNLOAD_FOLDER = "downloads"
os.makedirs("modules", exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

if not os.path.exists(COOKIE_FILE):
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        f.write("# Paste YouTube cookies here in Netscape format\n")

URL_RE = re.compile(r"(https?://[^\s]+)")
executor = ThreadPoolExecutor(max_workers=3)

# ================================
# کش YouTube
# ================================
YT_CACHE_FILE = os.path.join("modules", "yt_cache.json")
if not os.path.exists(YT_CACHE_FILE):
    with open(YT_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

with open(YT_CACHE_FILE, "r", encoding="utf-8") as f:
    try:
        YT_CACHE = json.load(f)
    except:
        YT_CACHE = {}

def save_yt_cache():
    with open(YT_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(YT_CACHE, f, indent=2, ensure_ascii=False)

# ================================
# ذخیره لینک‌ها برای انتخاب نوع و کیفیت
# ================================
pending_links = {}

# ================================
# دکمه افزودن ربات
# ================================
ADD_BTN = InlineKeyboardMarkup([
    [InlineKeyboardButton("➕ افزودن ربات به گروه", url="https://t.me/AFGR63_bot?startgroup=true")]
])

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
# دانلود ویدیو با حداکثر ارتفاع سفارشی
# ================================
def _download_video_sync(url, max_height: int = 720):
    fmt = f"bestvideo[height<={max_height}]+bestaudio/best[height<={max_height}]/best"
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
# مرحله ۲ و ۳ — انتخاب نوع و کیفیت با کش
# ================================
async def youtube_quality_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    chat_id = cq.message.chat_id
    await cq.answer()

    if update.effective_chat.type != "private":
        allowed = await is_admin(update, context)
        if not allowed:
            return

    url = pending_links.get(chat_id)
    if not url:
        return await cq.edit_message_text("❌ لینک معتبر یافت نشد.")

    choice = cq.data

    # ایجاد کش برای چت
    if str(chat_id) not in YT_CACHE:
        YT_CACHE[str(chat_id)] = {}

    # بررسی کش
    if url in YT_CACHE[str(chat_id)]:
        cached = YT_CACHE[str(chat_id)][url]
        if cached["type"] == "audio":
            await cq.edit_message_text("🎵 ارسال صوت از کش ...")
            await context.bot.send_audio(
                chat_id,
                cached["file_id"],
                caption=f"🎵 {cached.get('title','Audio')}",
                reply_markup=ADD_BTN if update.effective_chat.type == "private" else None
            )
        elif cached["type"] == "video":
            await cq.edit_message_text("🎬 ارسال ویدیو از کش ...")
            await context.bot.send_video(
                chat_id,
                cached["file_id"],
                caption=f"🎬 {cached.get('title','YouTube Video')} ({cached.get('quality','')})",
                reply_markup=ADD_BTN if update.effective_chat.type == "private" else None
            )
        return

    # -----------------------------
    # Audio — دانلود صوت
    # -----------------------------
    if choice == "yt_audio":
        await cq.edit_message_text("⬇ در حال دانلود صوت...")

        loop = asyncio.get_running_loop()
        info, mp3_file = await loop.run_in_executor(
            executor, _download_audio_sync, url
        )

        sent = await context.bot.send_audio(
            chat_id,
            audio=open(mp3_file, "rb"),
            caption=f"🎵 {info.get('title', 'Audio')}",
            reply_markup=ADD_BTN if update.effective_chat.type == "private" else None
        )

        # ذخیره در کش
        YT_CACHE[str(chat_id)][url] = {
            "file_id": sent.audio.file_id,
            "type": "audio",
            "title": info.get("title", "Audio")
        }
        save_yt_cache()

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
        q = choice.split("_")[1]
        max_height = int(q)
        quality_label = f"{q}p"

        await cq.edit_message_text(f"⬇ در حال دانلود کیفیت {quality_label} ...")

        loop = asyncio.get_running_loop()
        info, video_file = await loop.run_in_executor(
            executor, _download_video_sync, url, max_height
        )

        sent = await context.bot.send_video(
            chat_id,
            video=open(video_file, "rb"),
            caption=f"🎬 {info.get('title', 'YouTube Video')} ({quality_label})",
            reply_markup=ADD_BTN if update.effective_chat.type == "private" else None
        )

        # ذخیره در کش
        YT_CACHE[str(chat_id)][url] = {
            "file_id": sent.video.file_id,
            "type": "video",
            "title": info.get("title", "YouTube Video"),
            "quality": quality_label
        }
        save_yt_cache()

        if os.path.exists(video_file):
            os.remove(video_file)
        return
