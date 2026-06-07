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
CACHE_FILE = os.path.join(DATA_FOLDER, "soundcloud_cache.json")

os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

try:
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        MUSIC_CACHE = json.load(f)
except Exception:
    MUSIC_CACHE = {}

executor = ThreadPoolExecutor(max_workers=4)
track_store = {}

MUSIC_CAPTION = "🎵 دانلود موزیک با ربات @AFGR63_bot"

ADD_BTN = InlineKeyboardMarkup([
    [InlineKeyboardButton("➕ افزودن ربات به گروه", url="https://t.me/AFGR63_bot?startgroup=true")]
])

TRIGGERS = [
    "آهنگ ",
    "اهنگ ",
    "موزیک ",
    "music ",
    "musik ",
    "اغنية ",
    "أغنية ",
]

BASE_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "noprogress": True,
    "nopart": True,
    "noplaylist": True,
    "overwrites": True,
    "socket_timeout": 25,
    "retries": 5,
    "fragment_retries": 5,
    "concurrent_fragment_downloads": 8,
    "http_chunk_size": 8 * 1024 * 1024,
}


def save_cache():
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(MUSIC_CACHE, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def clean_file(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def cleanup_old_files():
    now = time.time()

    try:
        for name in os.listdir(DOWNLOAD_FOLDER):
            path = os.path.join(DOWNLOAD_FOLDER, name)

            if os.path.isfile(path) and now - os.path.getmtime(path) > 600:
                os.remove(path)
    except Exception:
        pass


def get_real_file(path):
    if path and os.path.exists(path):
        return path

    base = os.path.splitext(path)[0]

    for ext in ("mp3", "m4a", "webm", "opus", "ogg"):
        p = base + "." + ext
        if os.path.exists(p):
            return p

    return path


def _search_soundcloud(query):
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "socket_timeout": 20,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(f"scsearch10:{query}", download=False)


def _download_soundcloud(url):
    file_key = str(uuid.uuid4())

    opts = BASE_OPTS.copy()
    opts["outtmpl"] = os.path.join(DOWNLOAD_FOLDER, f"{file_key}.%(ext)s")

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)

        if not info:
            raise RuntimeError("اطلاعات موزیک دریافت نشد.")

        path = get_real_file(ydl.prepare_filename(info))

        if not path or not os.path.exists(path):
            raise FileNotFoundError("فایل موزیک ساخته نشد.")

        return info, path


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

    if not any(low.startswith(t.lower()) for t in TRIGGERS):
        return

    query = ""

    for trigger in TRIGGERS:
        if low.startswith(trigger.lower()):
            query = text[len(trigger):].strip()
            break

    if not query:
        return await update.message.reply_text("🎵 اسم آهنگ را بنویس.")

    msg = await update.message.reply_text("🔍 در حال جستجو در SoundCloud...")

    loop = asyncio.get_running_loop()

    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(executor, _search_soundcloud, query),
            timeout=30
        )
    except asyncio.TimeoutError:
        return await msg.edit_text("⏳ جستجو طول کشید. دوباره امتحان کن.")
    except Exception as e:
        return await msg.edit_text(f"❌ خطا در جستجو:\n{e}")

    entries = []

    for item in result.get("entries", []) if result else []:
        if not item:
            continue

        title = item.get("title") or "Unknown"
        url = item.get("url") or item.get("webpage_url")

        if not url:
            continue

        tid = str(item.get("id") or uuid.uuid4())
        entries.append((tid, title, url))

    if not entries:
        return await msg.edit_text("❌ آهنگی پیدا نشد.")

    entries = entries[:8]

    store_id = str(update.message.message_id)

    track_store[store_id] = {
        tid: {
            "title": title,
            "url": url
        }
        for tid, title, url in entries
    }

    keyboard = []

    for tid, title, _ in entries:
        keyboard.append([
            InlineKeyboardButton(
                title[:55],
                callback_data=f"music_select:{store_id}:{tid}"
            )
        ])

    await msg.edit_text(
        "🎶 یکی از نتایج را انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def music_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query

    if not cq:
        return

    await cq.answer("⚡ در حال آماده‌سازی...")

    try:
        _, store_id, tid = cq.data.split(":", 2)
    except Exception:
        return await cq.message.reply_text("❌ دکمه نامعتبر است.")

    track = track_store.get(store_id, {}).get(tid)

    if not track:
        return await cq.message.reply_text("❌ موزیک پیدا نشد. دوباره جستجو کن.")

    cache_key = "sc_" + tid
    chat_id = cq.message.chat.id

    if cache_key in MUSIC_CACHE:
        return await context.bot.send_audio(
            chat_id=chat_id,
            audio=MUSIC_CACHE[cache_key],
            caption=MUSIC_CAPTION,
            reply_markup=ADD_BTN if cq.message.chat.type == "private" else None,
        )

    msg = await cq.edit_message_text("⚡ در حال دانلود موزیک...")

    path = None

    try:
        cleanup_old_files()

        loop = asyncio.get_running_loop()

        info, path = await asyncio.wait_for(
            loop.run_in_executor(executor, _download_soundcloud, track["url"]),
            timeout=120
        )

        title = info.get("title") or track.get("title") or "Music"

        sent = await send_audio_file(
            context,
            chat_id,
            path,
            title,
            ADD_BTN if cq.message.chat.type == "private" else None
        )

        if not sent:
            await msg.edit_text("❌ فایل بزرگ است یا تلگرام قبول نکرد.")
            return

        if sent.audio:
            MUSIC_CACHE[cache_key] = sent.audio.file_id
            save_cache()

        await msg.delete()

    except asyncio.TimeoutError:
        await msg.edit_text("⏳ دانلود طول کشید. یک نتیجه دیگر انتخاب کن.")

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود:\n{e}")

    finally:
        clean_file(path)
        cleanup_old_files()
