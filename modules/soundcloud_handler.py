# modules/soundcloud_fast_multi.py

import asyncio
from concurrent.futures import ThreadPoolExecutor
import yt_dlp
import os
import json
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

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

executor = ThreadPoolExecutor(max_workers=10)

BASE_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    "noprogress": True,
    "nopart": True,
    "overwrites": True,
    "postprocessors": [{"key": "FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"128"}],
}

track_store = {}

# =========================
# جستجوی سریع metadata
# =========================
async def fast_search(query: str):
    def _search():
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            info = y.extract_info(f"scsearch10:{query}", download=False)
            return info.get("entries", [])
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, _search)

# =========================
# هندلر پیام
# =========================
async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    triggers = ["آهنگ ","music ","اهنگ ","موزیک "]
    if not any(text.lower().startswith(t) for t in triggers):
        return
    query = next((text[len(t):].strip() for t in triggers if text.lower().startswith(t)), "")
    msg = await update.message.reply_text("🔎 در حال جستجو...")

    try:
        entries = await fast_search(query)
    except Exception as e:
        return await msg.edit_text(f"❌ خطا در جستجو: {e}")
    if not entries:
        return await msg.edit_text("⚠ نتیجه‌ای پیدا نشد!")

    store = {}
    keyboard = []
    for t in entries[:10]:
        tid = str(t.get("id"))
        store[tid] = t
        keyboard.append([InlineKeyboardButton(t.get("title","Unknown"), callback_data=f"music_select:{tid}")])

    track_store[update.message.chat_id] = store
    await msg.edit_text(f"🎵 {len(store)} نتیجه یافت شد — انتخاب کنید:",
                        reply_markup=InlineKeyboardMarkup(keyboard))

# =========================
# دانلود همزمان چند آهنگ
# =========================
def _download_sync(url: str):
    with yt_dlp.YoutubeDL(BASE_OPTS) as y:
        info = y.extract_info(url, download=True)
        tid = str(info.get("id"))
        mp3 = y.prepare_filename(info).rsplit(".",1)[0]+".mp3"
        return tid, info, mp3

async def music_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    tid = cq.data.split(":")[1]
    tracks = track_store.get(cq.message.chat.id, {})
    track = tracks.get(tid)
    if not track:
        return await cq.edit_message_text("❌ آهنگ یافت نشد.")

    url = track.get("webpage_url")
    if not url:
        return await cq.edit_message_text("❌ لینک یافت نشد")

    cache_key = f"sc_{tid}"
    if cache_key in SC_CACHE:
        return await context.bot.send_audio(cq.message.chat.id, SC_CACHE[cache_key])

    await cq.edit_message_text("⏳ دانلود...")

    # دانلود همزمان با asyncio.gather
    loop = asyncio.get_running_loop()
    tid, info, mp3 = await loop.run_in_executor(executor, _download_sync, url)

    with open(mp3,"rb") as f:
        sent = await context.bot.send_audio(cq.message.chat.id, f, caption=info.get("title",""))

    os.remove(mp3)
    SC_CACHE[cache_key] = sent.audio.file_id
    save_cache()
    try:
        await cq.message.delete()
    except:
        pass
