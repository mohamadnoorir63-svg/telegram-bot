# modules/soundcloud_handler.py

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
# ThreadPool برای سرعت
# ================================
executor = ThreadPoolExecutor(max_workers=12)

# ================================
# جملات
# ================================
TXT = {
    "searching": "🔎 در حال جستجو...",
    "select": "🎵 {n} نتیجه یافت شد — انتخاب کنید:",
    "down": "⏳ دانلود...",
    "notfound": "⚠ نتیجه‌ای پیدا نشد! در حال جستجو در یوتیوب...",
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

track_store = {}  # ذخیره نتایج SoundCloud

# ================================
# چک کش محلی
# ================================
def cache_check(id_: str) -> Optional[str]:
    for file in os.listdir(DOWNLOAD_FOLDER):
        if file.startswith(id_) and file.endswith(".mp3"):
            return os.path.join(DOWNLOAD_FOLDER, file)
    return None

# ================================
# دانلود SoundCloud ultra-fast
# ================================
def _sc_download_sync(url: str):
    opts = BASE_OPTS.copy()
    opts["postprocessors"] = []  # بدون تبدیل MP3 → مستقیم لینک صوتی
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)
        tid = str(info.get("id"))
        cached = cache_check(tid)
        if cached:
            return info, cached
        fname = y.prepare_filename(info)
        return info, fname

# ================================
# دانلود fallback یوتیوب سریع
# ================================
def _youtube_fallback_fast(query: str):
    """
    دانلود fallback یوتیوب سریع با mp3 واقعی
    """
    opts = BASE_OPTS.copy()
    opts["format"] = "bestaudio/best"  # اصلاح شد
    opts["noplaylist"] = True
    opts["outtmpl"] = f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s"
    cookie_file = "modules/youtube_cookie.txt"
    if os.path.exists(cookie_file):
        opts["cookiefile"] = cookie_file
    opts["postprocessors"] = [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ]

    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(f"ytsearch1:{query}", download=True)
        if "entries" in info and info["entries"]:
            info = info["entries"][0]

        vid = str(info.get("id"))
        cached = cache_check(vid)
        if cached:
            return info, cached

        fname = y.prepare_filename(info)
        mp3 = fname.rsplit(".", 1)[0] + ".mp3"

        # اگر هنوز فایل وجود ندارد، خطا بده
        if not os.path.exists(mp3):
            raise FileNotFoundError(f"فایل mp3 برای {vid} پیدا نشد.")

        return info, mp3

# ================================
# هندلر پیام عادی با fallback یوتیوب
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

    # جستجوی SoundCloud
    def _search_sc():
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            return y.extract_info(f"scsearch10:{query}", download=False)

    try:
        result = await loop.run_in_executor(executor, _search_sc)
    except Exception:
        result = None

    # اگر نتیجه SoundCloud نبود → fallback یوتیوب
    if not result or not result.get("entries"):
        await msg.edit_text(TXT["notfound"])
        try:
            info, mp3 = await loop.run_in_executor(executor, _youtube_fallback_fast, query)
        except Exception as e:
            return await msg.edit_text(f"❌ خطا در جستجوی یوتیوب:\n{e}")

        cache_key = f"yt_{str(info.get('id'))}"
        chat_id = update.message.chat.id

        if cache_key in SC_CACHE:
            try: await msg.delete()
            except: pass
            return await update.message.reply_audio(SC_CACHE[cache_key], caption=f"🎵 {info.get('title', 'Music')}")

        try:
            with open(mp3, "rb") as f:
                sent = await update.message.reply_audio(f, caption=f"🎵 {info.get('title', 'Music')}")
        finally:
            if os.path.exists(mp3):
                os.remove(mp3)

        SC_CACHE[cache_key] = sent.audio.file_id
        save_cache()
        try: await msg.delete()
        except: pass
        return

    # SoundCloud نتیجه داد → دکمه انتخاب
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

    # ارسال از کش تلگرام
    if cache_key in SC_CACHE:
        try:
            await cq.edit_message_text("⚡ در حال ارسال از کش تلگرام...")
        except Exception:
            pass
        return await context.bot.send_audio(chat_id, SC_CACHE[cache_key])

    # دانلود SoundCloud
    msg = await cq.edit_message_text(TXT["down"])
    loop = asyncio.get_running_loop()
    try:
        info, mp3 = await loop.run_in_executor(executor, _sc_download_sync, track["webpage_url"])
    except Exception as e:
        return await msg.edit_text(f"❌ خطا در دانلود:\n{e}")

    # ارسال فایل
    try:
        with open(mp3, "rb") as f:
            sent = await context.bot.send_audio(chat_id, f, caption=info.get("title", ""))
    finally:
        if os.path.exists(mp3):
            os.remove(mp3)

    SC_CACHE[cache_key] = sent.audio.file_id
    save_cache()
    try: await msg.delete()
    except: pass
