import os
import json
import uuid
import time
import asyncio
import re
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

executor = ThreadPoolExecutor(max_workers=3)

try:
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        MUSIC_CACHE = json.load(f)
except Exception:
    MUSIC_CACHE = {}

MUSIC_CAPTION = "🎵 دانلود موزیک با ربات @AFGR63_bot"

ADD_BTN = InlineKeyboardMarkup([
    [InlineKeyboardButton("➕ افزودن ربات به گروه", url="https://t.me/AFGR63_bot?startgroup=true")]
])

URL_RE = re.compile(r"https?://\S+")


def save_cache():
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(MUSIC_CACHE, f, ensure_ascii=False, indent=2)


def cleanup_old_files():
    now = time.time()
    for name in os.listdir(DOWNLOAD_FOLDER):
        path = os.path.join(DOWNLOAD_FOLDER, name)
        try:
            if os.path.isfile(path) and now - os.path.getmtime(path) > 600:
                os.remove(path)
        except Exception:
            pass


def clean_file(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def find_file(file_key):
    for name in os.listdir(DOWNLOAD_FOLDER):
        if name.startswith(file_key):
            return os.path.join(DOWNLOAD_FOLDER, name)
    return None


def base_opts(file_key):
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "nopart": True,
        "noplaylist": True,
        "overwrites": True,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, f"{file_key}.%(ext)s"),
        "socket_timeout": 40,
        "retries": 10,
        "fragment_retries": 10,
        "http_chunk_size": 8 * 1024 * 1024,
        "concurrent_fragment_downloads": 8,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"]
            }
        },
    }

    if os.path.exists(COOKIE_FILE) and os.path.getsize(COOKIE_FILE) > 50:
        opts["cookiefile"] = COOKIE_FILE

    return opts


def download_opts(file_key, fmt_id):
    opts = base_opts(file_key)
    opts["format"] = fmt_id
    opts["postprocessors"] = [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ]
    return opts


def pick_format(info):
    formats = info.get("formats") or []

    real = []
    for f in formats:
        fmt_id = str(f.get("format_id") or "")
        if fmt_id.startswith("sb"):
            continue

        acodec = f.get("acodec")
        vcodec = f.get("vcodec")

        if acodec and acodec != "none":
            real.append(f)

    if not real:
        return None

    priority = ["140", "251", "250", "249", "18"]

    for p in priority:
        for f in real:
            if str(f.get("format_id")) == p:
                return p

    audio_only = [
        f for f in real
        if f.get("vcodec") == "none" and f.get("acodec") != "none"
    ]

    if audio_only:
        return str(audio_only[0].get("format_id"))

    return str(real[0].get("format_id"))


def download_youtube_audio(query):
    file_key = str(uuid.uuid4())

    probe_opts = base_opts(file_key)
    probe_opts["format"] = "best"

    with yt_dlp.YoutubeDL(probe_opts) as ydl:
        if query.startswith("http://") or query.startswith("https://"):
            info = ydl.extract_info(query, download=False)
        else:
            result = ydl.extract_info(f"ytsearch1:{query}", download=False)
            if not result or not result.get("entries"):
                raise RuntimeError("نتیجه‌ای از YouTube پیدا نشد.")
            info = result["entries"][0]

    if not info:
        raise RuntimeError("اطلاعات ویدیو دریافت نشد.")

    title = info.get("title") or query
    video_id = info.get("id") or file_key
    webpage_url = info.get("webpage_url") or info.get("original_url") or query

    fmt_id = pick_format(info)

    if not fmt_id:
        raise RuntimeError("برای این ویدیو فقط storyboard پیدا شد و صوت واقعی موجود نیست.")

    with yt_dlp.YoutubeDL(download_opts(file_key, fmt_id)) as ydl:
        ydl.extract_info(webpage_url, download=True)

    mp3_path = os.path.join(DOWNLOAD_FOLDER, f"{file_key}.mp3")

    if os.path.exists(mp3_path):
        path = mp3_path
    else:
        path = find_file(file_key)

    if not path or not os.path.exists(path):
        raise RuntimeError("فایل صوتی ساخته نشد.")

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
        "موزیک ",
        "music ",
        "musik ",
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

    url_match = URL_RE.search(query)

    if url_match:
        query_for_download = url_match.group(0)
        cache_key = "yt_url_" + query_for_download
    else:
        query_for_download = query
        cache_key = "yt_search_" + query.lower().strip()

    if cache_key in MUSIC_CACHE:
        return await context.bot.send_audio(
            chat_id=update.effective_chat.id,
            audio=MUSIC_CACHE[cache_key],
            caption=MUSIC_CAPTION,
            reply_markup=ADD_BTN if update.effective_chat.type == "private" else None,
        )

    msg = await update.message.reply_text("🎧 در حال دانلود از YouTube...")

    path = None

    try:
        cleanup_old_files()

        loop = asyncio.get_running_loop()
        info, path = await asyncio.wait_for(
            loop.run_in_executor(executor, download_youtube_audio, query_for_download),
            timeout=240
        )

        sent = await send_audio_file(
            context,
            update.effective_chat.id,
            path,
            info.get("title") or "Music",
            ADD_BTN if update.effective_chat.type == "private" else None
        )

        if not sent:
            await msg.edit_text("❌ فایل بزرگ است یا تلگرام قبول نکرد.")
            return

        if
