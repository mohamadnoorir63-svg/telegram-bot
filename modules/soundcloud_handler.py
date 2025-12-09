# modules/soundcloud_handler.py

import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
import yt_dlp
import json
from typing import Optional

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
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
        json.dump(SC_CACHE, f, ensure_ascii=False, indent=2)

# ================================
# ThreadPool ultra-fast
# ================================
executor = ThreadPoolExecutor(max_workers=20)  # نهایت concurrency

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
    "concurrent_fragment_downloads": 16,  # نهایت سرعت
    "fragment_retries": 4,
    "retries": 4,
    "postprocessors": [],  # تبدیل mp3 حذف شد برای سرعت
}

track_store = {}  # ذخیره نتایج جستجو

# ================================
# چک کش محلی
# ================================
def cache_check(id_: str) -> Optional[str]:
    for f in os.listdir(DOWNLOAD_FOLDER):
        if f.startswith(id_) and f.endswith(".mp3"):
            return os.path.join(DOWNLOAD_FOLDER, f)
    return None

# ================================
# دانلود ultra-fast
# ================================
def _sc_download_sync(url: str):
    opts = BASE_OPTS.copy()
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)
        tid = str(info.get("id"))
        cached = cache_check(tid)
        if cached:
            return info, cached
        fname = y.prepare_filename(info)
        return info, fname  # مستقیم بدون تبدیل

# ================================
# هندلر پیام
# ================================
async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    triggers = ["آهنگ ", "music ", "اهنگ ", "موزیک "]
    if not any(text.lower().startswith(t) for t in triggers):
        return

    query = next((text[len(t):].strip() for t in triggers if text.lower().startswith(t)), "")
    msg = await update.message.reply_text("🔎 در حال جستجو...")

    def _search():
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            return y.extract_info(f"scsearch10:{query}", download=False)

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(executor, _search)

    if not result or not result.get("entries"):
        return await msg.edit_text("⚠ نتیجه‌ای پیدا نشد!")

    # ذخیره نتایج و ساخت دکمه‌ها
    entries = {str(t["id"]): t for t in result["entries"]}
    track_store[update.message.message_id] = entries
    keyboard = [
        [InlineKeyboardButton(t["title"], callback_data=f"music_select:{update.message.message_id}:{tid}")]
        for tid, t in entries.items()
    ]

    await msg.edit_text(f"🎵 {len(entries)} نتیجه یافت شد — انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

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

    # ارسال از کش تلگرام اگر موجود است
    if cache_key in SC_CACHE:
        return await context.bot.send_audio(chat_id, SC_CACHE[cache_key])

    await cq.edit_message_text("⏳ دانلود...")

    url = track.get("webpage_url") or track.get("permalink_url")
    if not url:
        return await cq.edit_message_text("❌ لینک یافت نشد")

    loop = asyncio.get_running_loop()
    info, mp3 = await loop.run_in_executor(executor, _sc_download_sync, url)

    with open(mp3, "rb") as f:
        sent = await context.bot.send_audio(chat_id, f, caption=info.get("title", ""))

    os.remove(mp3)
    SC_CACHE[cache_key] = sent.audio.file_id
    save_cache()
    try:
        await cq.message.delete()
    except:
        pass
