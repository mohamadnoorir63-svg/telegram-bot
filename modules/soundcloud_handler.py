import os
import asyncio
import yt_dlp
from concurrent.futures import ThreadPoolExecutor
import json
from typing import Optional

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# ------------------------------
# سودو
# ------------------------------
SUDO_USERS = [8588347189]

# ------------------------------
# پوشه‌ها و کش
# ------------------------------
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

# ------------------------------
# ThreadPool برای سرعت
# ------------------------------
executor = ThreadPoolExecutor(max_workers=16)  # ultra-fast

# ------------------------------
# جملات
# ------------------------------
TXT = {
    "searching": "🔎 در حال جستجو...",
    "select": "🎵 {n} نتیجه یافت شد — انتخاب کنید:",
    "down": "⏳ دانلود...",
    "notfound": "⚠ نتیجه‌ای پیدا نشد!",
}

# ------------------------------
# تنظیمات yt_dlp ultra-fast
# ------------------------------
BASE_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "noprogress": True,
    "nopart": True,
    "noplaylist": True,
    "overwrites": True,
    "concurrent_fragment_downloads": 16,
    "postprocessors": [],
}

YOUTUBE_COOKIE_FILE = "modules/youtube_cookie.txt"  # ← مسیر کوکی یوتیوب

track_store = {}  # ذخیره نتایج SoundCloud و YouTube

# ------------------------------
# کش محلی
# ------------------------------
def cache_check(id_: str) -> Optional[str]:
    for file in os.listdir(DOWNLOAD_FOLDER):
        if file.startswith(id_) and file.endswith(".mp3"):
            return os.path.join(DOWNLOAD_FOLDER, file)
    return None

# ------------------------------
# دانلود ultra-fast
# ------------------------------
def _download_sync(url: str):
    opts = BASE_OPTS.copy()
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)
        tid = str(info.get("id"))
        cached = cache_check(tid)
        if cached:
            return info, cached
        fname = y.prepare_filename(info)
        return info, fname

# ------------------------------
# جستجوی SoundCloud و fallback YouTube
# ------------------------------
def _search_soundcloud(query: str):
    with yt_dlp.YoutubeDL({"quiet": True}) as y:
        info = y.extract_info(f"scsearch5:{query}", download=False)
        entries = info.get("entries") or []
        return entries

def _search_youtube(query: str):
    opts = BASE_OPTS.copy()
    if os.path.exists(YOUTUBE_COOKIE_FILE):
        opts["cookiefile"] = YOUTUBE_COOKIE_FILE
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(f"ytsearch5:{query}", download=False)
        entries = info.get("entries") or []
        return entries

# ------------------------------
# هندلر پیام عادی
# ------------------------------
async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    triggers = ["آهنگ ", "music ", "اهنگ ", "موزیک "]
    if not any(text.lower().startswith(t) for t in triggers):
        return

    query = next((text[len(t):].strip() for t in triggers if text.lower().startswith(t)), "")
    msg = await update.message.reply_text(TXT["searching"])

    loop = asyncio.get_running_loop()

    # ابتدا SoundCloud
    try:
        sc_entries = await loop.run_in_executor(executor, _search_soundcloud, query)
    except Exception:
        sc_entries = []

    # اگر چیزی نبود، fallback YouTube
    if not sc_entries:
        try:
            sc_entries = await loop.run_in_executor(executor, _search_youtube, query)
        except Exception:
            sc_entries = []

    if not sc_entries:
        return await msg.edit_text(TXT["notfound"])

    store = {}
    keyboard = []
    for t in sc_entries:
        tid = str(t.get("id"))
        store[tid] = t
        title = t.get("title") or "Unknown"
        keyboard.append([InlineKeyboardButton(title, callback_data=f"music_select:{tid}")])

    track_store[update.message.message_id] = store
    await msg.edit_text(TXT["select"].format(n=len(store)), reply_markup=InlineKeyboardMarkup(keyboard))

# ------------------------------
# دکمه انتخاب آهنگ
# ------------------------------
async def music_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()

    tid = cq.data.split(":")[1]
    tracks = track_store.get(cq.message.message_id, {})
    track = tracks.get(tid)
    if not track:
        return await cq.edit_message_text("❌ آهنگ یافت نشد.")

    cache_key = f"sc_{tid}"
    chat_id = cq.message.chat.id

    if cache_key in SC_CACHE:
        return await context.bot.send_audio(chat_id, SC_CACHE[cache_key])

    await cq.edit_message_text(TXT["down"])
    url = track.get("webpage_url")
    if not url:
        return await cq.edit_message_text("❌ لینک یافت نشد")

    loop = asyncio.get_running_loop()
    info, mp3 = await loop.run_in_executor(executor, _download_sync, url)

    with open(mp3, "rb") as f:
        sent = await context.bot.send_audio(chat_id, f, caption=info.get("title", ""))

    os.remove(mp3)
    SC_CACHE[cache_key] = sent.audio.file_id
    save_cache()
    try:
        await cq.message.delete()
    except:
        pass
