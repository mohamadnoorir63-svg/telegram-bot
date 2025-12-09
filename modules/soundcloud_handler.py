# modules/soundcloud_handler.py

import os
import asyncio
import yt_dlp
from concurrent.futures import ThreadPoolExecutor
import json
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes

# ================================
# پوشه‌ها و کش
# ================================
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

CACHE_FILE = "data/sc_cache.json"
os.makedirs("data", exist_ok=True)
if not os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

with open(CACHE_FILE, "r", encoding="utf-8") as f:
    try:
        SC_CACHE = json.load(f)
    except:
        SC_CACHE = {}

def save_cache():
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(SC_CACHE, f, ensure_ascii=False, indent=2)

# ================================
# ThreadPool ultra-fast کم‌مصرف
# ================================
executor = ThreadPoolExecutor(max_workers=4)

# ================================
# جملات
# ================================
TXT = {
    "searching": "🔎 در حال جستجو...",
    "down": "⏳ دانلود...",
    "notfound": "⚠ نتیجه‌ای پیدا نشد!",
}

# ================================
# تنظیمات yt_dlp
# ================================
BASE_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "noprogress": True,
    "nopart": True,
    "noplaylist": True,
    "overwrites": True,
    "concurrent_fragment_downloads": 4,
}

YOUTUBE_COOKIE_FILE = "modules/youtube_cookie.txt"
track_store = {}

# ================================
# چک کش محلی
# ================================
def cache_check(id_: str) -> Optional[str]:
    for file in os.listdir(DOWNLOAD_FOLDER):
        if file.startswith(id_) and file.endswith(".mp3"):
            return os.path.join(DOWNLOAD_FOLDER, file)
    return None

# ================================
# دانلود سریع
# ================================
def _download_sync(url: str):
    opts = BASE_OPTS.copy()
    opts["postprocessors"] = []
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)
        tid = str(info.get("id"))
        cached = cache_check(tid)
        if cached:
            return info, cached
        fname = y.prepare_filename(info)
        return info, fname

# ================================
# fallback یوتیوب
# ================================
def _youtube_fallback(query: str):
    opts = BASE_OPTS.copy()
    if os.path.exists(YOUTUBE_COOKIE_FILE):
        opts["cookiefile"] = YOUTUBE_COOKIE_FILE
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(f"ytsearch1:{query}", download=False)
        if "entries" in info and len(info["entries"]) > 0:
            info = info["entries"][0]
        else:
            raise Exception("یوتیوب چیزی پیدا نکرد")
        return info, None

# ================================
# هندلر پیام عادی
# ================================
async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text
    triggers = ["آهنگ ", "music ", "اهنگ ", "موزیک "]
    if not any(text.lower().startswith(t) for t in triggers):
        return
    query = next((text[len(t):].strip() for t in triggers if text.lower().startswith(t)), "")
    msg = await update.message.reply_text(TXT["searching"])
    loop = asyncio.get_running_loop()

    # ابتدا SoundCloud
    def _search_sc():
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            return y.extract_info(f"scsearch10:{query}", download=False)

    try:
        result = await loop.run_in_executor(executor, _search_sc)
    except:
        result = None

    if result and result.get("entries") and len(result["entries"]) > 0:
        track = result["entries"][0]  # اولین نتیجه
    else:
        # fallback یوتیوب
        try:
            track, _ = await loop.run_in_executor(executor, _youtube_fallback, query)
        except:
            await msg.edit_text(TXT["notfound"])
            return

    await msg.edit_text(TXT["down"])
    # دانلود مستقیم
    info, mp3 = await loop.run_in_executor(executor, _download_sync, track['webpage_url'])
    with open(mp3, "rb") as f:
        sent = await context.bot.send_audio(update.message.chat.id, f, caption=info.get("title", ""))
    os.remove(mp3)
    cache_key = f"sc_{info.get('id')}"
    SC_CACHE[cache_key] = sent.audio.file_id
    save_cache()
    await msg.delete()

# ================================
# هندلر inline ultra-fast مستقیم
# ================================
async def inline_sc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()
    if not query:
        return
    loop = asyncio.get_running_loop()

    # ابتدا SoundCloud
    def _search_sc():
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            return y.extract_info(f"scsearch6:{query}", download=False)

    try:
        result = await loop.run_in_executor(executor, _search_sc)
    except:
        result = None

    # گرفتن اولین نتیجه
    if result and result.get("entries") and len(result["entries"]) > 0:
        track = result["entries"][0]
    else:
        try:
            track, _ = await loop.run_in_executor(executor, _youtube_fallback, query)
        except:
            return  # چیزی پیدا نشد، چیزی ارسال نکن

    # دانلود مستقیم
    info, mp3 = await loop.run_in_executor(executor, _download_sync, track['webpage_url'])
    await context.bot.answer_inline_query(update.inline_query.id, results=[])  # خالی چون مستقیم میفرستیم
    await context.bot.send_audio(update.inline_query.from_user.id, open(mp3, "rb"), caption=info.get("title", ""))
    os.remove(mp3)
    SC_CACHE[f"sc_{info.get('id')}"] = info.get('id')
    save_cache()
