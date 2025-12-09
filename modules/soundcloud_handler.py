# modules/soundcloud_handler.py

import os
import asyncio
import yt_dlp
from concurrent.futures import ThreadPoolExecutor
import json
from typing import Optional
from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton,
    InlineQueryResultArticle, InputTextMessageContent
)
from telegram.ext import ContextTypes

# ================================
# سودو
# ================================
SUDO_USERS = [8588347189]

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
        json.dump(SC_CACHE, f, indent=2, ensure_ascii=False)

# ================================
# ThreadPool فوق سریع
# ================================
executor = ThreadPoolExecutor(max_workers=12)

# ================================
# yt_dlp تنظیمات
# ================================
BASE_OPTS = {
    "format": "bestaudio[ext=m4a]/bestaudio/best",
    "quiet": True,
    "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    "noprogress": True,
    "nopart": True,
    "retries": 5,
    "fragment_retries": 5,
    "concurrent_fragment_downloads": 8,
    "overwrites": True,
    "postprocessors": [
        {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
    ],
}

track_store = {}

TXT = {
    "searching": "🔎 جستجو...",
    "down": "⏳ دانلود...",
    "notfound": "⚠️ نتیجه‌ای پیدا نشد!",
}

# ================================
# کش سریع
# ================================
def cache_check(id_: str) -> Optional[str]:
    for file in os.listdir(DOWNLOAD_FOLDER):
        if file.startswith(id_) and file.endswith(".mp3") and os.path.getsize(os.path.join(DOWNLOAD_FOLDER, file)) > 1000:
            return os.path.join(DOWNLOAD_FOLDER, file)
    return None

# ================================
# دانلود SoundCloud سریع
# ================================
def _sc_download_sync(url: str):
    opts = BASE_OPTS.copy()
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)
        mp3_file = y.prepare_filename(info).rsplit(".", 1)[0] + ".mp3"
        if not os.path.exists(mp3_file) or os.path.getsize(mp3_file) < 1000:
            raise Exception("دانلود یا تبدیل mp3 شکست خورد")
        return info, mp3_file

# ================================
# هندلر inline ultra-fast
# ================================
async def inline_sc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()
    if not query:
        return

    def _search():
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            return y.extract_info(f"scsearch10:{query}", download=False)

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(executor, _search)
    results = []

    for t in result.get("entries", [])[:6]:
        tid = str(t["id"])
        track_store[f"inline_{tid}"] = t

        results.append(
            InlineQueryResultArticle(
                id=tid,
                title=t["title"],
                input_message_content=InputTextMessageContent(f"دانلود {t['title']}"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("دانلود", callback_data=f"music_inline:{tid}")]
                ])
            )
        )

    await update.inline_query.answer(results, cache_time=1)

# ================================
# دکمه دانلود inline ultra-fast
# ================================
async def music_inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer(cache_time=0)  # پاسخ فوری بدون تایم‌اوت
    tid = cq.data.replace("music_inline:", "")
    track = track_store.get(f"inline_{tid}")

    if not track:
        return await cq.edit_message_text("❌ آهنگ پیدا نشد.")

    chat_id = cq.message.chat.id
    cache_key = f"sc_{tid}"
    if cache_key in SC_CACHE:
        return await context.bot.send_audio(chat_id, SC_CACHE[cache_key])

    # دانلود و ارسال سریع
    loop = asyncio.get_running_loop()
    info, mp3 = await loop.run_in_executor(executor, _sc_download_sync, track["webpage_url"])

    with open(mp3, "rb") as f:
        sent = await context.bot.send_audio(chat_id, f, caption=info.get("title", "🎵 Music"))

    os.remove(mp3)
    SC_CACHE[cache_key] = sent.audio.file_id
    save_cache()
