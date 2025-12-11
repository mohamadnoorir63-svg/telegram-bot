import io
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
# تنظیمات
# ================================
URL_RE = re.compile(r"(https?://[^\s]+)")
executor = ThreadPoolExecutor(max_workers=3)
DOWNLOAD_FORMAT_AUDIO = "bestaudio/best"
DOWNLOAD_FORMAT_VIDEO = "bestvideo+bestaudio/best"

# ================================
# ذخیره لینک‌ها برای انتخاب نوع
# ================================
pending_links = {}

# ================================
# دکمه افزودن ربات (پیوی)
# ================================
def get_add_btn(chat_type):
    if chat_type == "private":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ افزودن ربات به گروه", url="https://t.me/AFGR63_bot?startgroup=true")]
        ])
    return None

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
# دانلود مستقیم به حافظه
# ================================
def _download_audio_bytes(url):
    opts = {
        "format": DOWNLOAD_FORMAT_AUDIO,
        "quiet": True,
        "noplaylist": True,
        "noprogress": True,
        "outtmpl": "%(id)s.%(ext)s"
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        audio_url = info["url"]
        # دانلود مستقیم روی BytesIO
        import requests
        r = requests.get(audio_url, stream=True)
        audio_bytes = io.BytesIO(r.content)
        audio_bytes.name = f"{info.get('title', 'audio')}.mp3"
        return info, audio_bytes

def _download_video_bytes(url):
    opts = {
        "format": DOWNLOAD_FORMAT_VIDEO,
        "quiet": True,
        "noplaylist": True,
        "noprogress": True,
        "outtmpl": "%(id)s.%(ext)s"
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        video_url = info["url"]
        import requests
        r = requests.get(video_url, stream=True)
        video_bytes = io.BytesIO(r.content)
        video_bytes.name = f"{info.get('title', 'video')}.mp4"
        return info, video_bytes

# ================================
# مرحله ۱ — دریافت لینک و انتخاب نوع
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

    # محدودیت گروه
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
# مرحله ۲ — دانلود و ارسال مستقیم
# ================================
async def youtube_quality_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    chat_id = cq.message.chat_id
    await cq.answer("در حال آماده‌سازی فایل ... ⏳", show_alert=False)

    if update.effective_chat.type != "private":
        allowed = await is_admin(update, context)
        if not allowed:
            return

    url = pending_links.get(chat_id)
    if not url:
        return await cq.message.reply_text("❌ لینک معتبر یافت نشد.")

    choice = cq.data
    loop = asyncio.get_running_loop()
    status_msg = await cq.message.reply_text("⬇ در حال دانلود مستقیم ...")

    if choice == "yt_audio":
        info, audio_bytes = await loop.run_in_executor(executor, _download_audio_bytes, url)
        await context.bot.send_audio(
            chat_id,
            audio=audio_bytes,
            caption=f"🎵 {info.get('title','Audio')}",
            reply_markup=get_add_btn(update.effective_chat.type)
        )
        await status_msg.delete()
        return

    if choice == "yt_video":
        info, video_bytes = await loop.run_in_executor(executor, _download_video_bytes, url)
        await context.bot.send_video(
            chat_id,
            video=video_bytes,
            caption=f"🎬 {info.get('title','Video')}",
            reply_markup=get_add_btn(update.effective_chat.type)
        )
        await status_msg.delete()
        return
