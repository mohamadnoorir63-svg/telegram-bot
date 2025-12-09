# modules/soundcloud_inline.py

import os
import asyncio
import yt_dlp
from concurrent.futures import ThreadPoolExecutor
import json

from telegram import (
    Update,
    InlineQueryResultCachedAudio,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import ContextTypes

# ================================
# سودوها
# ================================
SUDO_USERS = [8588347189]

# ================================
# تنظیمات
# ================================
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

COOKIE_FILE = "modules/youtube_cookie.txt"
executor = ThreadPoolExecutor(max_workers=3)

# کش فایل‌ها
CACHE_FILE = "data/sc_inline_cache.json"
os.makedirs("data", exist_ok=True)
if not os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

with open(CACHE_FILE, "r", encoding="utf-8") as f:
    try:
        SC_CACHE = json.load(f)
    except json.JSONDecodeError:
        SC_CACHE = {}

def save_cache():
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(SC_CACHE, f, ensure_ascii=False, indent=2)

# ================================
# yt_dlp تنظیمات
# ================================
BASE_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    "noprogress": True,
    "nopart": True,
    "retries": 8,
    "fragment_retries": 8,
    "concurrent_fragment_downloads": 4,
    "overwrites": True,
    "postprocessors": [
        {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "128"}
    ],
}

# ================================
# کش محلی mp3
# ================================
def cache_check(id_: str):
    for file in os.listdir(DOWNLOAD_FOLDER):
        if file.startswith(id_) and file.endswith(".mp3"):
            return os.path.join(DOWNLOAD_FOLDER, file)
    return None

# ================================
# دانلود SoundCloud
# ================================
def _sc_download_sync(url: str):
    opts = BASE_OPTS.copy()
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)
        track_id = str(info.get("id"))
        cached = cache_check(track_id)
        if cached:
            return info, cached
        fname = y.prepare_filename(info)
        mp3 = fname.rsplit(".", 1)[0] + ".mp3"
        return info, mp3

# ================================
# fallback یوتیوب
# ================================
def _youtube_fallback_sync(query: str):
    opts = BASE_OPTS.copy()
    if os.path.exists(COOKIE_FILE):
        opts["cookiefile"] = COOKIE_FILE
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(f"ytsearch1:{query}", download=True)
        if "entries" in info:
            info = info["entries"][0]
        vid = str(info.get("id"))
        cached = cache_check(vid)
        if cached:
            return info, cached
        fname = y.prepare_filename(info)
        mp3 = fname.rsplit(".", 1)[0] + ".mp3"
        return info, mp3

# ================================
# هندلر Inline
# ================================
async def inline_sc_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()
    if not query:
        return

    loop = asyncio.get_running_loop()

    def _search_sc():
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            return y.extract_info(f"scsearch5:{query}", download=False)

    try:
        sc_info = await loop.run_in_executor(executor, _search_sc)
    except Exception:
        sc_info = None

    results = []

    if sc_info and sc_info.get("entries"):
        tracks = sc_info["entries"]
    else:
        try:
            info, mp3 = await loop.run_in_executor(executor, _youtube_fallback_sync, query)
            tracks = [info]
        except Exception:
            tracks = []

    for t in tracks:
        track_id = str(t.get("id"))
        cache_key = f"sc_{track_id}"
        if cache_key in SC_CACHE:
            file_id = SC_CACHE[cache_key]
            results.append(
                InlineQueryResultCachedAudio(
                    id=track_id,
                    audio_file_id=file_id,
                    title=t.get("title") or "Music",
                    performer=t.get("uploader") or ""
                )
            )
            continue

        # دانلود mp3 قبل از ارسال
        try:
            info, mp3 = await loop.run_in_executor(executor, _sc_download_sync, t.get("webpage_url"))
        except Exception:
            continue

        # ارسال Inline Audio
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(
            "➕ افزودن به گروه",
            url="https://t.me/AFGR63_bot?startgroup=true"
        )]]) if update.effective_user else None

        with open(mp3, "rb") as f:
            sent = await context.bot.send_audio(
                update.effective_user.id,
                f,
                caption=f"🎵 {info.get('title')}\n\n📥 <a href='https://t.me/AFGR63_bot'>دانلود موزیک</a>",
                parse_mode="HTML",
                reply_markup=keyboard if keyboard else None
            )
        SC_CACHE[cache_key] = sent.audio.file_id
        save_cache()
        if os.path.exists(mp3):
            os.remove(mp3)

        results.append(
            InlineQueryResultCachedAudio(
                id=track_id,
                audio_file_id=sent.audio.file_id,
                title=info.get("title") or "Music",
                performer=info.get("uploader") or ""
            )
        )

    await update.inline_query.answer(results, cache_time=1)
