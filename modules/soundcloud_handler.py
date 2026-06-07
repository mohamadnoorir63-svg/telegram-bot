import os
import json
import uuid
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

import yt_dlp
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

DATA_FOLDER = "data"
DOWNLOAD_FOLDER = "downloads"
CACHE_FILE = os.path.join(DATA_FOLDER, "youtube_music_cache.json")
COOKIE_FILE = os.path.join("modules", "youtube_cookie.txt")

os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs("modules", exist_ok=True)

if not os.path.exists(COOKIE_FILE):
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        f.write("# Paste YouTube cookies here in Netscape format\n")

try:
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        MUSIC_CACHE = json.load(f)
except Exception:
    MUSIC_CACHE = {}

executor = ThreadPoolExecutor(max_workers=4)

MUSIC_CAPTION = "🎵 دانلود موزیک با ربات @AFGR63_bot"

ADD_BTN = InlineKeyboardMarkup([
    [InlineKeyboardButton("➕ افزودن ربات به گروه", url="https://t.me/AFGR63_bot?startgroup=true")]
])


def save_cache():
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(MUSIC_CACHE, f, ensure_ascii=False)


def clean_file(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def cleanup_old_files():
    now = time.time()

    for name in os.listdir(DOWNLOAD_FOLDER):
        path = os.path.join(DOWNLOAD_FOLDER, name)

        try:
            if os.path.isfile(path) and now - os.path.getmtime(path) > 600:
                os.remove(path)
        except Exception:
            pass


def get_real_file(path):
    if path and os.path.exists(path):
        return path

    base = os.path.splitext(path)[0]

    for ext in ["mp3", "m4a", "webm", "opus"]:
        p = base + "." + ext
        if os.path.exists(p):
            return p

    return path


def youtube_opts(file_key):
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "nopart": True,
        "noplaylist": True,
        "overwrites": True,
        "format": "bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, f"{file_key}.%(ext)s"),
        "socket_timeout": 30,
        "retries": 5,
        "fragment_retries": 5,
        "concurrent_fragment_downloads": 8,
        "http_chunk_size": 8 * 1024 * 1024,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    if os.path.exists(COOKIE_FILE):
        opts["cookiefile"] = COOKIE_FILE

    return opts


def _youtube_download_sync(query):
    file_key = str(uuid.uuid4())

    with yt_dlp.YoutubeDL(youtube_opts(file_key)) as ydl:
        info = ydl.extract_info(f"ytsearch1:{query}", download=True)

        if "entries" in info and info["entries"]:
            info = info["entries"][0]

        if not info:
            raise RuntimeError("نتیجه‌ای از YouTube پیدا نشد.")

        title = info.get("title") or query
        video_id = info.get("id") or file_key

        path = os.path.join(DOWNLOAD_FOLDER, f"{file_key}.mp3")

        if not os.path.exists(path):
            path = get_real_file(ydl.prepare_filename(info))

        if not os.path.exists(path):
            raise FileNotFoundError("فایل MP3 ساخته نشد.")

        return {
            "id": video_id,
            "title": title,
        }, path


async def send_audio_file(context, chat_id, path, title, reply_markup=None):
    if not path or not os.path.exists(path):
        return None

    if os.path.getsize(path) > 49 * 1024 * 1024:
        return None

    with open(path, "rb") as audio:
        return await context.bot.send_audio(
            chat_id=chat_id,
            audio=audio,
            title=title or "Music",
            caption=MUSIC_CAPTION,
            reply_markup=reply_markup,
            read_timeout=180,
            write_timeout=180,
            connect_timeout=60,
        )


async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    low = text.lower()

    triggers = [
        "آهنگ ",
        "اهنگ ",
        "music ",
        "musik ",
        "موزیک ",
        "اغنية ",
        "أغنية ",
    ]

    if not any(low.startswith(t.lower()) for t in triggers):
        return

    query = ""

    for t in triggers:
        if low.startswith(t.lower()):
            query = text[len(t):].strip()
            break

    if not query:
        return await update.message.reply_text("🎵 اسم آهنگ را بنویس.")

    cache_key = "yt_" + query.lower().strip()

    if cache_key in MUSIC_CACHE:
        return await context.bot.send_audio(
            chat_id=update.effective_chat.id,
            audio=MUSIC_CACHE[cache_key],
            caption=MUSIC_CAPTION,
            reply_markup=ADD_BTN if update.effective_chat.type == "private" else None,
        )

    msg = await update.message.reply_text("🔍 در حال جستجو و دانلود از YouTube...")

    path = None

    try:
        cleanup_old_files()

        loop = asyncio.get_running_loop()

        info, path = await asyncio.wait_for(
            loop.run_in_executor(executor, _youtube_download_sync, query),
            timeout=160
        )

        sent = await send_audio_file(
            context,
            update.effective_chat.id,
            path,
            info.get("title") or "Music",
            ADD_BTN if update.effective_chat.type == "private" else None
        )

        if not sent:
            return await msg.edit_text("❌ فایل بزرگ است یا تلگرام قبول نکرد.")

        if sent.audio:
            MUSIC_CACHE[cache_key] = sent.audio.file_id
            save_cache()

        await msg.delete()

    except asyncio.TimeoutError:
        await msg.edit_text("⏳ دانلود طول کشید. یک آهنگ دیگر امتحان کن.")

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود از YouTube:\n{e}")

    finally:
        clean_file(path)


async def music_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    if cq:
        await cq.answer("این نسخه فقط با جستجوی مستقیم از YouTube کار می‌کند.", show_alert=True)
