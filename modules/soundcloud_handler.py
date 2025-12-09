# modules/soundcloud_handler.py

import os
import asyncio
import yt_dlp
from concurrent.futures import ThreadPoolExecutor
import json
from typing import Optional

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from telegram.ext import ContextTypes

# ================================
# سودو
# ================================
SUDO_USERS = [8588347189]

# ================================
# پوشه‌ها + کش
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
        json.dump(SC_CACHE, f, indent=2, ensure_ascii=False)

# ================================
# ThreadPool ultra-fast
# ================================
executor = ThreadPoolExecutor(max_workers=12)

# ================================
# جملات
# ================================
TXT = {
    "searching": "🔎 در حال جستجو...",
    "select": "🎵 {n} نتیجه یافت شد — انتخاب کنید:",
    "down": "⏳ دانلود...",
    "notfound": "⚠ نتیجه‌ای پیدا نشد!",
}

# ================================
# تنظیمات yt_dlp ultra-fast
# ================================
BASE_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "noprogress": True,
    "nopart": True,
    "noplaylist": True,
    "overwrites": True,
    "concurrent_fragment_downloads": 16,
}

YOUTUBE_COOKIE = "modules/youtube_cookie.txt"

track_store = {}  # ذخیره نتایج پیام و inline

# ================================
# چک کش محلی
# ================================
def cache_check(id_: str) -> Optional[str]:
    for file in os.listdir(DOWNLOAD_FOLDER):
        if file.startswith(id_) and file.endswith(".mp3"):
            return os.path.join(DOWNLOAD_FOLDER, file)
    return None

# ================================
# دانلود SoundCloud/YouTube ultra-fast
# ================================
def _download_sync(url: str):
    opts = BASE_OPTS.copy()
    opts["postprocessors"] = []
    if "youtube.com" in url or "youtu.be" in url:
        if os.path.exists(YOUTUBE_COOKIE):
            opts["cookiefile"] = YOUTUBE_COOKIE
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)
        tid = str(info.get("id"))
        cached = cache_check(tid)
        if cached:
            return info, cached
        fname = y.prepare_filename(info)
        return info, fname

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

    # ---------- جستجو SoundCloud ----------
    def _sc_search():
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            return y.extract_info(f"scsearch10:{query}", download=False)

    loop = asyncio.get_running_loop()
    try:
        result = await loop.run_in_executor(executor, _sc_search)
    except:
        result = None

    # ---------- اگر SoundCloud نتیجه نداشت → YouTube ----------
    if not result or not result.get("entries"):
        def _yt_search():
            opts = BASE_OPTS.copy()
            if os.path.exists(YOUTUBE_COOKIE):
                opts["cookiefile"] = YOUTUBE_COOKIE
            with yt_dlp.YoutubeDL(opts) as y:
                info = y.extract_info(f"ytsearch5:{query}", download=False)
                if "entries" in info:
                    return info["entries"]
                return []
        try:
            result_entries = await loop.run_in_executor(executor, _yt_search)
        except:
            result_entries = []
        if not result_entries:
            return await msg.edit_text(TXT["notfound"])
        entries = {str(t["id"]): t for t in result_entries}
    else:
        entries = {str(t["id"]): t for t in result["entries"]}

    track_store[update.message.message_id] = entries

    keyboard = [
        [InlineKeyboardButton(t["title"], callback_data=f"music_select:{update.message.message_id}:{tid}")]
        for tid, t in entries.items()
    ]
    await msg.edit_text(TXT["select"].format(n=len(entries)), reply_markup=InlineKeyboardMarkup(keyboard))

# ================================
# دکمه انتخاب آهنگ
# ================================
async def music_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()

    _, msg_id, tid = cq.data.split(":")
    msg_id = int(msg_id)
    tracks = track_store.get(msg_id, {})
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

# ================================
# هندلر جستجوی inline
# ================================
async def inline_sc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()
    if not query:
        return

    def _sc_inline():
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            return y.extract_info(f"scsearch6:{query}", download=False)

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(executor, _sc_inline)

    if not result or not result.get("entries"):
        # fallback یوتیوب
        def _yt_inline():
            opts = BASE_OPTS.copy()
            if os.path.exists(YOUTUBE_COOKIE):
                opts["cookiefile"] = YOUTUBE_COOKIE
            with yt_dlp.YoutubeDL(opts) as y:
                info = y.extract_info(f"ytsearch5:{query}", download=False)
                if "entries" in info:
                    return info["entries"]
                return []
        result_entries = await loop.run_in_executor(executor, _yt_inline)
    else:
        result_entries = result["entries"]

    results = []
    for t in result_entries[:6]:
        tid = str(t["id"])
        track_store[f"inline_{tid}"] = t
        results.append(
            InlineQueryResultArticle(
                id=tid,
                title=t.get("title", "Unknown"),
                input_message_content=InputTextMessageContent(f"دانلود {t.get('title','')}"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("دانلود", callback_data=f"music_inline:{tid}")]
                ])
            )
        )
    await update.inline_query.answer(results, cache_time=5)

# ================================
# دکمه دانلود در حالت inline
# ================================
async def music_inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()

    tid = cq.data.replace("music_inline:", "")
    track = track_store.get(f"inline_{tid}")
    if not track:
        return await cq.edit_message_text("❌ آهنگ یافت نشد.")

    await cq.edit_message_text(TXT["down"])
    url = track.get("webpage_url")
    if not url:
        return await cq.edit_message_text("❌ لینک یافت نشد")

    loop = asyncio.get_running_loop()
    info, mp3 = await loop.run_in_executor(executor, _download_sync, url)

    with open(mp3, "rb") as f:
        sent = await context.bot.send_audio(cq.message.chat.id, f, caption=info.get("title", ""))

    os.remove(mp3)
