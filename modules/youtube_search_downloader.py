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
TEMP_FILE_MAX_AGE = 600

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.dirname(COOKIE_FILE), exist_ok=True)

URL_RE = re.compile(r"(https?://[^\s]+)")
executor = ThreadPoolExecutor(max_workers=3)

pending_links = {}
download_queue = asyncio.Queue()


def ensure_cookie_file():
    if not os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, "w", encoding="utf-8") as f:
            f.write(
                "# Netscape HTTP Cookie File\n"
                "# Paste your YouTube cookies here\n"
            )


ensure_cookie_file()


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

    for filename in os.listdir(DOWNLOAD_FOLDER):
        path = os.path.join(DOWNLOAD_FOLDER, filename)

        try:
            if os.path.isfile(path):
                age = now - os.path.getmtime(path)
                if age > TEMP_FILE_MAX_AGE:
                    os.remove(path)
        except Exception:
            pass


def find_file(video_id: str, extensions: list[str]) -> str | None:
    for ext in extensions:
        path = os.path.join(DOWNLOAD_FOLDER, f"{video_id}.{ext}")
        if os.path.exists(path):
            return path

    return None


def base_ydl_opts():
    return {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "retries": 10,
        "fragment_retries": 10,
        "nopart": True,
        "overwrites": True,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"]
            }
        },
    }


def audio_opts():
    opts = base_ydl_opts()

    opts.update({
        "format": "140/251/250/249/bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    })

    return opts


def video_opts():
    opts = base_ydl_opts()

    opts.update({
        "format": "18/best[ext=mp4]/best",
        "merge_output_format": "mp4",
    })

    return opts


def _download_audio_sync(url: str):
    with yt_dlp.YoutubeDL(audio_opts()) as ydl:
        info = ydl.extract_info(url, download=True)

    if not info or not info.get("id"):
        raise RuntimeError("استخراج اطلاعات صوت ناموفق بود.")

    path = find_file(info["id"], ["mp3", "m4a", "webm", "opus"])

    if not path:
        raise FileNotFoundError("فایل صوتی ساخته نشد.")

    return info, path


def _download_video_sync(url: str):
    with yt_dlp.YoutubeDL(video_opts()) as ydl:
        info = ydl.extract_info(url, download=True)

    if not info or not info.get("id"):
        raise RuntimeError("استخراج اطلاعات ویدیو ناموفق بود.")

    path = find_file(info["id"], ["mp4", "webm", "mkv"])

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
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def youtube_download_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query

    if not cq or not cq.message:
        return

    await cq.answer()

    chat_id = cq.message.chat.id
    user_id = cq.from_user.id

    if cq.message.chat.type != "private":
        try:
            member = await context.bot.get_chat_member(chat_id, user_id)
            allowed = user_id in SUDO_USERS or member.status in ("creator", "administrator")
        except Exception:
            allowed = False

        if not allowed:
            await cq.answer("⛔ فقط مدیران گروه مجاز هستند.", show_alert=True)
            return

    url = pending_links.get(chat_id)

    if not url:
        await cq.edit_message_text("❌ لینک پیدا نشد. دوباره لینک یوتیوب را بفرست.")
        return

    await download_queue.put({
        "chat_id": chat_id,
        "message_id": cq.message.message_id,
        "url": url,
        "mode": cq.data,
    })

    await cq.edit_message_text("⏳ لینک شما به صف دانلود اضافه شد. لطفاً منتظر بمانید...")


async def send_file_size_error(bot, chat_id, path, text):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

    await bot.send_message(chat_id, text)


async def download_worker(bot):
    while True:
        item = await download_queue.get()

        chat_id = item["chat_id"]
        message_id = item["message_id"]
        url = item["url"]
        mode = item["mode"]

        cleanup_temp()

        try:
            loop = asyncio.get_running_loop()

            if mode == "yt_audio":
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text="🎵 در حال دانلود و تبدیل به MP3...",
                )

                info, file_path = await loop.run_in_executor(
                    executor,
                    _download_audio_sync,
                    url,
                )

                if os.path.getsize(file_path) > MAX_FILE_SIZE:
                    await send_file_size_error(
                        bot,
                        chat_id,
                        file_path,
                        "❌ حجم فایل صوتی بیشتر از 800MB است.",
                    )
                    continue

                title = info.get("title") or "YouTube Audio"

                with open(file_path, "rb") as f:
                    await bot.send_audio(
                        chat_id=chat_id,
                        audio=f,
                        title=title,
                        caption=f"🎵 {title}",
                        read_timeout=180,
                        write_timeout=180,
                        connect_timeout=60,
                    )

                os.remove(file_path)

            elif mode == "yt_video":
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text="🎬 در حال دانلود ویدیو MP4...",
                )

                info, file_path = await loop.run_in_executor(
                    executor,
                    _download_video_sync,
                    url,
                )

                if os.path.getsize(file_path) > MAX_FILE_SIZE:
                    await send_file_size_error(
                        bot,
                        chat_id,
                        file_path,
                        "❌ حجم ویدیو بیشتر از 800MB است.",
                    )
                    continue

                title = info.get("title") or "YouTube Video"

                with open(file_path, "rb") as f:
                    await bot.send_video(
                        chat_id=chat_id,
                        video=f,
                        caption=f"🎬 {title}",
                        supports_streaming=True,
                        read_timeout=180,
                        write_timeout=180,
                        connect_timeout=60,
                    )

                os.remove(file_path)

            try:
                await bot.delete_message(chat_id=chat_id, message_id=message_id)
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
