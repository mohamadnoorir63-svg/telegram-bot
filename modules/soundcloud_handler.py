# ================================
# فایل: modules/soundcloud_handler.py (Tidal)
# ================================

import os
import asyncio
import yt_dlp
from concurrent.futures import ThreadPoolExecutor
import json
from typing import Optional

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
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
# ThreadPool برای سرعت
# ================================
executor = ThreadPoolExecutor(max_workers=12)

# ================================
# جملات
# ================================
TXT = {
    "searching": "🔎 در حال جستجو...",
    "down": "⏳ دانلود موزیک از ربات دانلود آهنگ ...",
    "notfound": "⌛ ممکن است تا 15 ثانیه طول بکشد",
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
    "ignoreerrors": True,
}

track_store = {}  # ذخیره نتایج جستجو

# ================================
# چک کش محلی
# ================================
def cache_check(id_: str) -> Optional[str]:
    for file in os.listdir(DOWNLOAD_FOLDER):
        if file.startswith(id_) and file.endswith(".mp3"):
            return os.path.join(DOWNLOAD_FOLDER, file)
    return None

# ================================
# دانلود از Tidal
# ================================
def _tidal_download_sync(url: str):
    opts = BASE_OPTS.copy()
    cookie_file = "modules/tidal_cookie.txt"
    if os.path.exists(cookie_file):
        opts["cookiefile"] = cookie_file
    opts["postprocessors"] = [
        {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "128"}
    ]
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)
        if not info:
            return None, None
        tid = str(info.get("id", ""))
        cached = cache_check(tid)
        if cached:
            return info, cached
        mp3_file = y.prepare_filename(info).rsplit(".", 1)[0] + ".mp3"
        if not os.path.exists(mp3_file):
            return None, None
        return info, mp3_file

# ================================
# هندلر پیام اصلی
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

    # لینک مستقیم Tidal (فرض: کاربر لینک Tidal می‌دهد یا جستجو)
    tidal_url = f"https://tidal.com/search?q={query}"

    try:
        info, mp3 = await loop.run_in_executor(executor, _tidal_download_sync, tidal_url)
    except Exception as e:
        return await msg.edit_text(f"❌ خطا در دانلود Tidal:\n{e}")

    if not info or not mp3:
        return await msg.edit_text("❌ چیزی پیدا نشد!")

    cache_key = f"tidal_{info.get('id')}"
    chat_id = update.message.chat.id

    buttons = None
    if update.effective_chat.type == "private":
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("افزودن به گروه", url=f"https://t.me/AFGR63_bot?startgroup=true")]
        ])

    # ارسال فایل
    if cache_key in SC_CACHE:
        try: await msg.delete()
        except: pass
        return await update.message.reply_audio(
            SC_CACHE[cache_key],
            caption="🎵 ربات دانلود آهنگ",
            reply_markup=buttons
        )

    try:
        with open(mp3, "rb") as f:
            sent = await update.message.reply_audio(
                f,
                caption="🎵 ربات دانلود آهنگ",
                reply_markup=buttons
            )
    finally:
        if os.path.exists(mp3):
            os.remove(mp3)

    SC_CACHE[cache_key] = sent.audio.file_id
    save_cache()
    try: await msg.delete()
    except: pass
