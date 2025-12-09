# modules/soundcloud_handler.py

import os
import asyncio
import yt_dlp
import json
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.ext import ContextTypes

SUDO_USERS = [8588347189]

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

executor = ThreadPoolExecutor(max_workers=6)

BASE_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    "noprogress": True,
    "nopart": True,
    "retries": 4,
    "fragment_retries": 4,
    "concurrent_fragment_downloads": 6,
    "overwrites": True,
    "postprocessors": [
        {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "128"}
    ],
}

track_store = {}

# ————— جستجوی سریع با HTTP API ساوندکلاد —————
SOUNDCLOUD_CLIENT_ID = "YOUR_CLIENT_ID"  # ← اگر دارید
SOUNDCLOUD_SEARCH_URL = "https://api.soundcloud.com/tracks"

async def sc_search(query: str, limit: int = 6):
    params = {
        "q": query,
        "limit": limit,
        "client_id": SOUNDCLOUD_CLIENT_ID
    }
    async with aiohttp.ClientSession() as sess:
        async with sess.get(SOUNDCLOUD_SEARCH_URL, params=params, timeout=10) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()
            return data  # لیست ترک‌ها

def cache_check(id_: str) -> Optional[str]:
    for f in os.listdir(DOWNLOAD_FOLDER):
        if f.startswith(id_) and f.endswith(".mp3"):
            return os.path.join(DOWNLOAD_FOLDER, f)
    return None

def _sc_download_sync(url: str):
    with yt_dlp.YoutubeDL(BASE_OPTS) as y:
        info = y.extract_info(url, download=True)
        tid = str(info.get("id"))
        cached = cache_check(tid)
        if cached:
            return info, cached
        fname = y.prepare_filename(info)
        mp3 = fname.rsplit(".", 1)[0] + ".mp3"
        return info, mp3

async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    triggers = ["آهنگ ", "music ", "اهنگ ", "موزیک "]
    if not any(text.lower().startswith(t) for t in triggers):
        return
    query = next((text[len(t):].strip() for t in triggers if text.lower().startswith(t)), "")
    msg = await update.message.reply_text("🔎 در حال جستجو...")
    try:
        results = await sc_search(query, limit=6)
    except Exception as e:
        return await msg.edit_text(f"❌ خطا در جستجو: {e}")
    if not results:
        return await msg.edit_text("⚠ نتیجه‌ای پیدا نشد!")

    # ذخیره نتایج
    store = {}
    keyboard = []
    for t in results:
        tid = str(t.get("id"))
        store[tid] = t
        title = t.get("title") or "Unknown"
        keyboard.append([InlineKeyboardButton(title, callback_data=f"music_select:{tid}")])

    track_store[update.message.chat_id] = store
    await msg.edit_text(f"🎵 {len(store)} نتیجه یافت شد — انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

async def music_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    tid = cq.data.split(":")[1]
    tracks = track_store.get(cq.message.chat.id, {})
    track = tracks.get(tid)
    if not track:
        return await cq.edit_message_text("❌ آهنگ یافت نشد.")

    cache_key = f"sc_{tid}"
    if cache_key in SC_CACHE:
        return await context.bot.send_audio(cq.message.chat.id, SC_CACHE[cache_key])

    await cq.edit_message_text("⏳ دانلود...")
    url = track.get("permalink_url")
    if not url:
        return await cq.edit_message_text("❌ لینک یافت نشد")

    loop = asyncio.get_running_loop()
    info, mp3 = await loop.run_in_executor(executor, _sc_download_sync, url)
    with open(mp3, "rb") as f:
        sent = await context.bot.send_audio(cq.message.chat.id, f, caption=info.get("title", ""))
    os.remove(mp3)
    SC_CACHE[cache_key] = sent.audio.file_id
    save_cache()
    try:
        await cq.message.delete()
    except:
        pass
