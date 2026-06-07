import os
import re
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

import yt_dlp
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

SUDO_USERS = [8588347189]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, "downloads")
COOKIE_FILE = os.path.join(BASE_DIR, "modules", "youtube_cookie.txt")

MAX_FILE_SIZE = 800 * 1024 * 1024

os.makedirs(os.path.dirname(COOKIE_FILE), exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# ==========================

# ==========================

COOKIE_DATA = r"""
# Netscape HTTP Cookie File
# https://curl.haxx.se/rfc/cookie_spec.html
# This is a generated file! Do not edit.



"""

with open(COOKIE_FILE, "w", encoding="utf-8") as f:
    f.write(COOKIE_DATA.strip() + "\n")

# ==========================

URL_RE = re.compile(r"(https?://[^\s]+)")
executor = ThreadPoolExecutor(max_workers=4)

pending_links = {}
download_queue = asyncio.Queue()


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user

    if not chat or not user:
        return False

    if chat.type == "private":
        return True

    if user.id in SUDO_USERS:
        return True

    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ("creator", "administrator")
    except Exception:
        return False


def cleanup_temp():
    now = time.time()
    for name in os.listdir(DOWNLOAD_FOLDER):
        path = os.path.join(DOWNLOAD_FOLDER, name)
        try:
            if os.path.isfile(path) and now - os.path.getmtime(path) > 600:
                os.remove(path)
        except Exception:
            pass


def audio_opts():
    return {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "format": "140/251/250/249/bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
        "retries": 10,
        "fragment_retries": 10,
        "nopart": True,
        "overwrites": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"]
            }
        },
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }


def video_opts():
    return {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "format": "18/best",
        "merge_output_format": "mp4",
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
        "retries": 10,
        "fragment_retries": 10,
        "nopart": True,
        "overwrites": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"]
            }
        },
    }


def find_file(video_id, exts):
    for ext in exts:
        path = os.path.join(DOWNLOAD_FOLDER, f"{video_id}.{ext}")
        if os.path.exists(path):
            return path
    return None


def _download_audio_sync(url: str):
    with yt_dlp.YoutubeDL(audio_opts()) as ydl:
        info = ydl.extract_info(url, download=True)

    if not info or "id" not in info:
        raise RuntimeError("استخراج اطلاعات صوت ناموفق بود.")

    video_id = info["id"]
    path = find_file(video_id, ["mp3", "m4a", "webm", "opus"])

    if not path:
        raise FileNotFoundError("فایل صوتی ساخته نشد.")

    return info, path


def _download_video_sync(url: str):
    with yt_dlp.YoutubeDL(video_opts()) as ydl:
        info = ydl.extract_info(url, download=True)

    if not info or "id" not in info:
        raise RuntimeError("استخراج اطلاعات ویدیو ناموفق بود.")

    video_id = info["id"]
    path = find_file(video_id, ["mp4", "webm", "mkv"])

    if not path:
        raise FileNotFoundError("فایل ویدیو ساخته نشد.")

    return info, path


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

    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    pending_links[update.effective_chat.id] = url

    keyboard = [
        [
            InlineKeyboardButton("🎵 دانلود صوت MP3", callback_data="yt_audio"),
            InlineKeyboardButton("🎬 دانلود ویدیو MP4", callback_data="yt_video"),
        ]
    ]

    await update.message.reply_text(
        "⬇️ نوع دانلود را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def youtube_download_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query

    if not cq:
        return

    await cq.answer()

    chat_id = cq.message.chat.id

    if cq.message.chat.type != "private":
        member = await context.bot.get_chat_member(chat_id, cq.from_user.id)
        if cq.from_user.id not in SUDO_USERS and member.status not in ("creator", "administrator"):
            return await cq.answer("⛔ فقط مدیران گروه مجاز هستند.", show_alert=True)

    url = pending_links.get(chat_id)

    if not url:
        return await cq.edit_message_text("❌ لینک پیدا نشد. دوباره لینک یوتیوب را بفرست.")

    await download_queue.put({
        "chat_id": chat_id,
        "message_id": cq.message.message_id,
        "url": url,
        "mode": cq.data,
    })

    await cq.edit_message_text("⏳ لینک شما به صف دانلود اضافه شد. لطفاً منتظر بمانید...")


async def download_worker(bot):
    while True:
        item = await download_queue.get()

        chat_id = item["chat_id"]
        message_id = item["message_id"]
        url = item["url"]
        mode = item["mode"]

        cleanup_temp()
        loop = asyncio.get_running_loop()

        try:
            if mode == "yt_audio":
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text="🎵 در حال دانلود و تبدیل به MP3..."
                )

                info, audio_path = await loop.run_in_executor(
                    executor,
                    _download_audio_sync,
                    url
                )

                if os.path.getsize(audio_path) > MAX_FILE_SIZE:
                    os.remove(audio_path)
                    await bot.send_message(chat_id, "❌ حجم فایل صوتی بیشتر از 800MB است.")
                    continue

                title = info.get("title") or "YouTube Audio"

                with open(audio_path, "rb") as f:
                    await bot.send_audio(
                        chat_id=chat_id,
                        audio=f,
                        title=title,
                        caption=f"🎵 {title}",
                        read_timeout=180,
                        write_timeout=180,
                        connect_timeout=60,
                    )

                os.remove(audio_path)

            elif mode == "yt_video":
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text="🎬 در حال دانلود ویدیو MP4..."
                )

                info, video_path = await loop.run_in_executor(
                    executor,
                    _download_video_sync,
                    url
                )

                if os.path.getsize(video_path) > MAX_FILE_SIZE:
                    os.remove(video_path)
                    await bot.send_message(chat_id, "❌ حجم ویدیو بیشتر از 800MB است.")
                    continue

                title = info.get("title") or "YouTube Video"

                with open(video_path, "rb") as f:
                    await bot.send_video(
                        chat_id=chat_id,
                        video=f,
                        caption=f"🎬 {title}",
                        supports_streaming=True,
                        read_timeout=180,
                        write_timeout=180,
                        connect_timeout=60,
                    )

                os.remove(video_path)

            try:
                await bot.delete_message(chat_id, message_id)
            except Exception:
                pass

        except Exception as e:
            try:
                await bot.send_message(chat_id, f"❌ خطا در دانلود:\n{e}")
            except Exception:
                pass

        finally:
            cleanup_temp()
            download_queue.task_done()
