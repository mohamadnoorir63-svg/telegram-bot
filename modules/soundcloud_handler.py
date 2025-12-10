import os
import asyncio
import yt_dlp
from concurrent.futures import ThreadPoolExecutor
import io
import json
from typing import Optional

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# ================================
# سودو
# ================================
SUDO_USERS = [8588347189]

# ================================
# کش
# ================================
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
# ThreadPool برای async
# ================================
executor = ThreadPoolExecutor(max_workers=12)

# ================================
# جملات
# ================================
TXT = {
    "searching": "🔎",
    "select": "🎵:",
    "down": "⏳ دانلود...",
    "notfound": "⌛",
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
    "concurrent_fragment_downloads": 16,
}

track_store = {}

# ================================
# دانلود مستقیم به حافظه
# ================================
def _sc_download_sync_bytes(url: str) -> tuple:
    opts = BASE_OPTS.copy()
    opts["postprocessors"] = []
    # استفاده از BytesIO
    opts["outtmpl"] = os.path.join("downloads", "%(id)s.%(ext)s")
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)
        tid = str(info.get("id"))
        fname = y.prepare_filename(info)
        with open(fname, "rb") as f:
            audio_bytes = f.read()
        os.remove(fname)
        return info, audio_bytes

async def _sc_download_bytes(url: str):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, _sc_download_sync_bytes, url)
# ================================
# fallback YouTube
# ================================
async def _youtube_fallback(query: str) -> tuple:
    """نسخه async که از ThreadPool استفاده می‌کند"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, _youtube_fallback_sync, query)

def _youtube_fallback_sync(query: str) -> tuple:
    """دانلود مستقیم از یوتیوب با yt_dlp و تبدیل به mp3"""
    opts = BASE_OPTS.copy()
    opts["concurrent_fragment_downloads"] = 20

    # اگر کوکی یوتیوب موجود بود استفاده شود
    cookie_file = "modules/youtube_cookie.txt"
    if os.path.exists(cookie_file):
        opts["cookiefile"] = cookie_file

    opts["format"] = "bestaudio/best"
    opts["noplaylist"] = True
    opts["postprocessors"] = [
        {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
    ]

    with yt_dlp.YoutubeDL(opts) as y:
        try:
            # جستجوی اول فقط یک نتیجه
            info = y.extract_info(f"ytsearch1:{query}", download=True)
        except Exception as e:
            raise RuntimeError(f"خطا در yt_dlp: {e}")

        if "entries" in info and info["entries"]:
            info = info["entries"][0]

        vid = str(info.get("id"))
        # بررسی کش محلی
        cached = cache_check(vid)
        if cached:
            return info, cached

        mp3 = y.prepare_filename(info).rsplit(".", 1)[0] + ".mp3"
        if not os.path.exists(mp3):
            raise FileNotFoundError(f"فایل mp3 برای {vid} پیدا نشد.")

        return info, mp3
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
    def _search_sc():
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            return y.extract_info(f"scsearch10:{query}", download=False)

    try:
        result = await loop.run_in_executor(executor, _search_sc)
    except:
        result = None

    if not result or not result.get("entries"):
        return await msg.edit_text(TXT["notfound"])

    entries = {str(t["id"]): t for t in result["entries"]}
    track_store[update.message.message_id] = entries
    keyboard = [
        [InlineKeyboardButton(t["title"], callback_data=f"music_select:{update.message.message_id}:{tid}")]
        for tid, t in entries.items()
    ]
    await msg.edit_text(TXT["select"].format(n=len(entries)), reply_markup=InlineKeyboardMarkup(keyboard))
    

# دکمه انتخاب آهنگ
# ================================
async def music_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    _, msg_id, tid = cq.data.split(":")
    msg_id = int(msg_id)
    track = track_store.get(msg_id, {}).get(tid)
    if not track:
        return await cq.edit_message_text("❌ آهنگ یافت نشد.")

    cache_key = f"sc_{tid}"
    chat_id = cq.message.chat.id
    if cache_key in SC_CACHE:
        return await context.bot.send_audio(chat_id, SC_CACHE[cache_key])

    msg = await cq.edit_message_text(TXT["down"])
    info, audio_bytes = await _sc_download_bytes(track["webpage_url"])

    # ارسال مستقیم از حافظه (نه Voice)
    audio_io = io.BytesIO(audio_bytes)
    audio_io.name = f"{info.get('title','music')}.mp3"
    sent = await context.bot.send_audio(chat_id, audio_io, caption=info.get("title",""))

    SC_CACHE[cache_key] = sent.audio.file_id
    save_cache()
    await msg.delete()
