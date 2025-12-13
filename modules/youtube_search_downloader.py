import os
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor

import yt_dlp
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# ====================================
# CONFIG
# ====================================

SUDO_USERS = [8588347189]
COOKIE_FILE = "modules/youtube_cookie.txt"
DOWNLOAD_FOLDER = "downloads"

os.makedirs("modules", exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

URL_RE = re.compile(r"(https?://[^\s]+)")
executor = ThreadPoolExecutor(max_workers=20)
pending_links = {}

# ====================================
# ADMIN CHECK
# ====================================

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

# ====================================
# YT-DLP OPTIONS
# ====================================

def video_opts(max_height):
    return {
        "quiet": True,
        "cookiefile": COOKIE_FILE,
        "format": f"bv*[height<={max_height}]/b[height<={max_height}]/best",
        "merge_output_format": "mp4",
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
        "concurrent_fragment_downloads": 16,
        "http_chunk_size": 8 * 1024 * 1024,
        "retries": 10,
        "fragment_retries": 10,
        "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
    }

def audio_opts():
    return {
        "quiet": True,
        "cookiefile": COOKIE_FILE,
        "format": "ba/best",
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
    }

# ====================================
# SAFE DOWNLOAD FUNCTIONS
# ====================================

def safe_download_video(url, req_height):
    heights = [req_height, 480, 360, 240]  # fallback
    for h in heights:
        try:
            with yt_dlp.YoutubeDL(video_opts(h)) as y:
                info = y.extract_info(url, download=True)
                if not info or not info.get("id"):
                    continue
                vid = info["id"]
                path = f"{DOWNLOAD_FOLDER}/{vid}.mp4"
                if os.path.exists(path):
                    return info, path, h
        except Exception:
            continue
    raise RuntimeError("هیچ کیفیت قابل دانلودی پیدا نشد")

def safe_download_audio(url):
    with yt_dlp.YoutubeDL(audio_opts()) as y:
        info = y.extract_info(url, download=True)
        if not info or not info.get("id"):
            raise RuntimeError("دانلود صوت ناموفق بود")
        path = f"{DOWNLOAD_FOLDER}/{info['id']}.mp3"
        if not os.path.exists(path):
            raise RuntimeError("فایل صوت ساخته نشد")
    return info, path

# ====================================
# TELEGRAM HANDLERS
# ====================================

async def youtube_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    m = URL_RE.search(update.message.text)
    if not m:
        return

    url = m.group(1)
    if "youtube" not in url and "youtu.be" not in url:
        return

    if update.effective_chat.type != "private" and not await is_admin(update, context):
        return

    pending_links[update.effective_chat.id] = url

    await update.message.reply_text(
        "⬇️ انتخاب نوع دانلود:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎵 صوت MP3", callback_data="yt_audio")],
            [InlineKeyboardButton("🎬 ویدیو MP4", callback_data="yt_video")],
        ])
    )

async def youtube_quality_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    chat_id = cq.message.chat_id
    await cq.answer("⏳ در حال پردازش...")

    url = pending_links.get(chat_id)
    if not url:
        return await cq.edit_message_text("❌ لینک منقضی شده")

    loop = asyncio.get_running_loop()

    if cq.data == "yt_audio":
        await cq.edit_message_text("🎵 دانلود صوت...")
        try:
            info, path = await loop.run_in_executor(executor, safe_download_audio, url)
        except Exception as e:
            return await context.bot.send_message(chat_id, f"❌ خطا:\n{e}")

        await context.bot.send_document(
            chat_id,
            document=open(path, "rb"),
            caption=f"🎵 {info.get('title','')}"
        )
        os.remove(path)
        return

    if cq.data == "yt_video":
        await cq.edit_message_text(
            "📺 کیفیت:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("720p", callback_data="v_720")],
                [InlineKeyboardButton("480p", callback_data="v_480")],
                [InlineKeyboardButton("360p", callback_data="v_360")],
            ])
        )
        return

    if cq.data.startswith("v_"):
        q = int(cq.data.split("_")[1])
        await cq.edit_message_text(f"🎬 دانلود {q}p ...")
        try:
            info, path, real_q = await loop.run_in_executor(executor, safe_download_video, url, q)
        except Exception as e:
            return await context.bot.send_message(chat_id, f"❌ خطا:\n{e}")

        await context.bot.send_document(
            chat_id,
            document=open(path, "rb"),
            caption=f"🎬 {info.get('title','')} ({real_q}p)"
        )
        os.remove(path)
        return

# ====================================
# START BOT
# ====================================

if __name__ == "__main__":
    from telegram.ext import ApplicationBuilder
    import logging

    logging.basicConfig(level=logging.INFO)
    TOKEN = os.environ.get("BOT_TOKEN")  # ست کن

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), youtube_search_handler))
    app.add_handler(CallbackQueryHandler(youtube_quality_handler))

    print("🤖 Bot is running...")
    app.run_polling()
