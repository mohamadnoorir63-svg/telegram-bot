import re
import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
import yt_dlp
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

SUDO_USERS = [8588347189]
COOKIE_FILE = "modules/youtube_cookie.txt"
DOWNLOAD_FOLDER = "downloads"
URL_RE = re.compile(r"(https?://[^\s]+)")
executor = ThreadPoolExecutor(max_workers=2)
pending_links = {}

os.makedirs("modules", exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

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
    if update.effective_chat.type != "private" and not await is_admin(update, context):
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

async def youtube_download_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    chat_id = cq.message.chat_id

    if update.effective_chat.type != "private" and not await is_admin(update, context):
        return

    url = pending_links.get(chat_id)
    if not url:
        return await cq.edit_message_text("❌ لینک یافت نشد")

    await cq.edit_message_text("⬇️ در حال پردازش و دانلود...")

    loop = asyncio.get_running_loop()
    if cq.data == "yt_audio":
        await loop.run_in_executor(executor, download_audio, url, context, chat_id)
    elif cq.data == "yt_video":
        await loop.run_in_executor(executor, download_video, url, context, chat_id)

def download_audio(url, context, chat_id):
    ydl_opts = {
        "cookiefile": COOKIE_FILE,
        "format": "bestaudio/best",
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
        "quiet": True,
        "noplaylist": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            audio_file = ydl.prepare_filename(info).rsplit(".",1)[0]+".mp3
            asyncio.run_coroutine_threadsafe(
                context.bot.send_audio(chat_id, audio=open(audio_file,"rb"), caption=f"🎵 {info.get('title','Audio')}"),
                asyncio.get_event_loop()
            ).result()
            os.remove(audio_file)
    except Exception as e:
        asyncio.run_coroutine_threadsafe(
            context.bot.send_message(chat_id, f"❌ دانلود صوت ناموفق بود\n{e}"),
            asyncio.get_event_loop()
        )

def download_video(url, context, chat_id):
    ydl_opts = {
        "cookiefile": COOKIE_FILE,
        "format": "bestvideo[height<=720]+bestaudio/best/best",
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
        "quiet": True,
        "noplaylist": True,
        "merge_output_format": "mp4"
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_file = ydl.prepare_filename(info)
            asyncio.run_coroutine_threadsafe(
                context.bot.send_video(chat_id, video=open(video_file,"rb"), caption=f"🎬 {info.get('title','Video')}"),
                asyncio.get_event_loop()
            ).result()
            os.remove(video_file)
    except Exception as e:
        asyncio.run_coroutine_threadsafe(
            context.bot.send_message(chat_id, f"❌ دانلود ویدیو ناموفق بود\n{e}"),
            asyncio.get_event_loop()
        )
