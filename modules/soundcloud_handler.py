import os
import asyncio
import yt_dlp
from concurrent.futures import ThreadPoolExecutor
import json
from typing import Optional

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# ---------------------------
# پوشه‌ها و کش
# ---------------------------
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

# ---------------------------
# ThreadPool ultra-fast
# ---------------------------
executor = ThreadPoolExecutor(max_workers=12)

# ---------------------------
# جملات
# ---------------------------
TXT = {
    "searching": "🔎 در حال جستجو...",
    "select": "🎵 {n} نتیجه یافت شد — انتخاب کنید:",
    "down": "⏳ دانلود...",
    "notfound": "⚠ نتیجه‌ای پیدا نشد!",
}

# ---------------------------
# تنظیمات yt_dlp ultra-fast
# ---------------------------
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

# مسیر کوکی یوتیوب
YOUTUBE_COOKIE_FILE = "modules/youtube_cookie.txt"

# ذخیره موقت Track ها
track_store = {}

# ---------------------------
# چک کش محلی
# ---------------------------
def cache_check(id_: str) -> Optional[str]:
    for file in os.listdir(DOWNLOAD_FOLDER):
        if file.startswith(id_) and file.endswith(".mp3"):
            return os.path.join(DOWNLOAD_FOLDER, file)
    return None

# ---------------------------
# دانلود ultra-fast
# ---------------------------
def _download_sync(url: str):
    opts = BASE_OPTS.copy()
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)
        tid = str(info.get("id"))
        cached = cache_check(tid)
        if cached:
            return info, cached
        fname = y.prepare_filename(info)
        mp3 = fname.rsplit(".", 1)[0] + ".mp3"
        return info, mp3

# ---------------------------
# دانلود fallback یوتیوب
# ---------------------------
def _youtube_fallback_sync(query: str):
    opts = BASE_OPTS.copy()
    if os.path.exists(YOUTUBE_COOKIE_FILE):
        opts["cookiefile"] = YOUTUBE_COOKIE_FILE
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

# ---------------------------
# هندلر پیام عادی
# ---------------------------
async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    triggers = ["آهنگ ", "music ", "اهنگ ", "موزیک "]
    if not any(text.lower().startswith(t) for t in triggers):
        return
    query = next((text[len(t):].strip() for t in triggers if text.lower().startswith(t)), "")
    msg = await update.message.reply_text(TXT["searching"])

    # جستجو SoundCloud ultra-fast
    def _sc_search():
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            return y.extract_info(f"scsearch10:{query}", download=False)

    loop = asyncio.get_running_loop()
    try:
        sc_info = await loop.run_in_executor(executor, _sc_search)
        entries = sc_info.get("entries", []) if sc_info else []
    except:
        entries = []

    if not entries:
        # fallback یوتیوب
        try:
            info, mp3 = await loop.run_in_executor(executor, _youtube_fallback_sync, query)
            with open(mp3, "rb") as f:
                sent = await context.bot.send_audio(update.effective_chat.id, f, caption=info.get("title",""))
            os.remove(mp3)
            await msg.delete()
            return
        except:
            return await msg.edit_text(TXT["notfound"])

    # ذخیره Track ها
    track_store.clear()
    keyboard = []
    for t in entries[:6]:
        tid = str(t.get("id"))
        track_store[tid] = t
        keyboard.append([InlineKeyboardButton(t.get("title","Unknown"), callback_data=f"music_select:{tid}")])

    await msg.edit_text(TXT["select"].format(n=len(track_store)), reply_markup=InlineKeyboardMarkup(keyboard))

# ---------------------------
# دکمه انتخاب آهنگ
# ---------------------------
async def music_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    tid = cq.data.split(":")[1]
    track = track_store.get(tid)
    if not track:
        return await cq.edit_message_text("❌ آهنگ یافت نشد.")

    cache_key = f"sc_{tid}"
    chat_id = cq.message.chat.id

    if cache_key in SC_CACHE:
        return await context.bot.send_audio(chat_id, SC_CACHE[cache_key])

    await cq.edit_message_text(TXT["down"])
    url = track.get("webpage_url") or track.get("url")
    if not url:
        return await cq.edit_message_text("❌ لینک یافت نشد")

    loop = asyncio.get_running_loop()
    info, mp3 = await loop.run_in_executor(executor, _download_sync, url)
    with open(mp3, "rb") as f:
        sent = await context.bot.send_audio(chat_id, f, caption=info.get("title",""))
    os.remove(mp3)

    SC_CACHE[cache_key] = sent.audio.file_id
    save_cache()
    try:
        await cq.message.delete()
    except:
        pass
