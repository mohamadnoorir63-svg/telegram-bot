import os
import re
import yt_dlp
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from concurrent.futures import ThreadPoolExecutor

SUDO_USERS = [8588347189]

INSTAGRAM_COOKIES = """# Netscape HTTP Cookie File ..."""
COOKIE_FILE = "insta_cookie.txt"
with open(COOKIE_FILE, "w", encoding="utf-8") as f:
    f.write(INSTAGRAM_COOKIES.strip())

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

URL_RE = re.compile(r"(https?://[^\s]+)")
executor = ThreadPoolExecutor(max_workers=3)

def get_add_btn(chat_type):
    if chat_type == "private":
        return InlineKeyboardMarkup([[InlineKeyboardButton("➕ افزودن ربات به گروه", url="https://t.me/AFGR63_bot?startgroup=true")]])
    return None

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

async def instagram_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    m = URL_RE.search(text)
    if not m:
        return
    url = m.group(1)
    if "instagram.com" not in url:
        return
    if update.effective_chat.type != "private":
        allowed = await is_admin(update, context)
        if not allowed:
            return

    msg = await update.message.reply_text("📥 در حال بررسی لینک اینستاگرام...")

    ydl_opts = {
        "quiet": True,
        "cookiefile": COOKIE_FILE,
        "format": "bestvideo+bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
        "merge_output_format": "mp4",
    }

    try:
        loop = asyncio.get_running_loop()
        def run_ydl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=True)
        info = await loop.run_in_executor(executor, run_ydl)

        entries = info.get("entries", [info])
        for entry in entries:
            file_path = yt_dlp.YoutubeDL(ydl_opts).prepare_filename(entry)
            if os.path.exists(file_path):
                ext = file_path.split(".")[-1].lower()
                if ext in ["mp4", "mov", "webm"]:
                    await update.message.reply_video(video=open(file_path, "rb"), caption=entry.get("title",""))
                elif ext in ["jpg", "jpeg", "png", "webp"]:
                    await update.message.reply_photo(photo=open(file_path, "rb"), caption=entry.get("title",""))

                # ساخت MP3
                audio_file = file_path.rsplit(".",1)[0]+".mp3"
                if not os.path.exists(audio_file):
                    ydl_audio_opts = {
                        "quiet": True,
                        "cookiefile": COOKIE_FILE,
                        "format": "bestaudio/best",
                        "postprocessors": [{"key":"FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"192"}],
                        "outtmpl": audio_file,
                    }
                    def run_audio_ydl():
                        with yt_dlp.YoutubeDL(ydl_audio_opts) as ydl_audio:
                            ydl_audio.extract_info(url, download=True)
                    await loop.run_in_executor(executor, run_audio_ydl)
                if os.path.exists(audio_file):
                    await update.message.reply_audio(audio=open(audio_file,"rb"), caption=entry.get("title",""))

        await msg.delete()
        if update.effective_chat.type == "private":
            await update.message.reply_text("➕ افزودن ربات به گروه:", reply_markup=get_add_btn(update.effective_chat.type))

    except Exception as e:
        await msg.edit_text(f"❌ نتوانستم دانلود کنم.\n⚠️ خطا: {e}")
