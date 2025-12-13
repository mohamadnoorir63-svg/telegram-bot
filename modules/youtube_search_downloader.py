import re
import asyncio
import subprocess
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from concurrent.futures import ThreadPoolExecutor
import yt_dlp

SUDO_USERS = [8588347189]
COOKIE_FILE = "modules/youtube_cookie.txt"
URL_RE = re.compile(r"(https?://[^\s]+)")
executor = ThreadPoolExecutor(max_workers=1)
pending_links = {}

# ==========================
# Helper: Admin check
# ==========================
async def is_admin(update, context):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private" or user.id in SUDO_USERS:
        return True
    try:
        admins = await context.bot.get_chat_administrators(chat.id)
        return user.id in [a.user.id for a in admins]
    except:
        return False

# ==========================
# STEP 1: Receive Link
# ==========================
async def youtube_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    text = update.message.text
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
        [InlineKeyboardButton("🎬 Video (MP4)", callback_data="yt_video")]
    ]
    await update.message.reply_text(
        "⬇️ نوع دانلود را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==========================
# STEP 2: Stream Download
# ==========================
async def youtube_download_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    chat_id = cq.message.chat_id
    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return
    url = pending_links.get(chat_id)
    if not url:
        return await cq.edit_message_text("❌ لینک یافت نشد")
    await cq.edit_message_text("⬇️ در حال پردازش و دانلود...")
    loop = asyncio.get_running_loop()

    if cq.data == "yt_audio":
        await loop.run_in_executor(executor, stream_audio, url, context, chat_id)
    elif cq.data == "yt_video":
        await loop.run_in_executor(executor, stream_video, url, context, chat_id)

# ==========================
# STREAM AUDIO
# ==========================
def stream_audio(url, context, chat_id):
    ydl_opts = {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "format": "bestaudio/best",
        "outtmpl": "-",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "noplaylist": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Audio')
            # ffmpeg pipe
            process = subprocess.Popen(
                ["ffmpeg", "-i", url, "-f", "mp3", "pipe:1"],
                stdout=subprocess.PIPE
            )
            context.bot.send_audio(chat_id, audio=process.stdout, caption=f"🎵 {title}")
            process.stdout.close()
            process.wait()
    except Exception as e:
        asyncio.run(context.bot.send_message(chat_id, f"❌ دانلود صوت ناموفق بود\n{e}"))

# ==========================
# STREAM VIDEO
# ==========================
def stream_video(url, context, chat_id):
    ydl_opts = {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "format": "bestvideo[height<=720]+bestaudio/best",
        "outtmpl": "-",
        "noplaylist": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Video')
            # ffmpeg pipe
            process = subprocess.Popen(
                ["ffmpeg", "-i", url, "-f", "mp4", "pipe:1"],
                stdout=subprocess.PIPE
            )
            context.bot.send_video(chat_id, video=process.stdout, caption=f"🎬 {title}")
            process.stdout.close()
            process.wait()
    except Exception as e:
        asyncio.run(context.bot.send_message(chat_id, f"❌ دانلود ویدیو ناموفق بود\n{e}"))
