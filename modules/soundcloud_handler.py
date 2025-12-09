import os
import asyncio
import yt_dlp
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import json
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# ================================
# سودو + پوشه‌ها
# ================================
SUDO_USERS = [8588347189]

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

CACHE_FILE = "data/sc_cache.json"
os.makedirs("data", exist_ok=True)
if not os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "w") as f:
        json.dump({}, f)
with open(CACHE_FILE, "r") as f:
    try: SC_CACHE = json.load(f)
    except: SC_CACHE = {}

def save_cache():
    with open(CACHE_FILE, "w") as f:
        json.dump(SC_CACHE, f, indent=2, ensure_ascii=False)

executor = ThreadPoolExecutor(max_workers=40)
track_store = {}

TXT = {
    "searching": "🔎 جستجو با سرعت نور...",
    "select": "🎵 {n} نتیجه پیدا شد — انتخاب کن:",
    "down": "⚡ دانلود موشکی...",
    "notfound": "⚠️ نتیجه‌ای پیدا نشد!"
}

# ================================
# yt-dlp سریع بدون تبدیل
# ================================
BASE_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "noprogress": True,
    "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    "retries": 20,
    "fragment_retries": 20,
    "concurrent_fragment_downloads": 50,
    "nopart": True,
    "overwrites": True,
    "postprocessors": []  # بدون FFmpeg = سرعت ×3
}

# ================================
# کش محلی
# ================================
def cache_check(id_):
    for f in os.listdir(DOWNLOAD_FOLDER):
        if f.startswith(id_):
            return os.path.join(DOWNLOAD_FOLDER, f)
    return None

# ================================
# دانلود مستقیم chunk به chunk با aiohttp
# ================================
async def download_aio(url, filename):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            with open(filename, "wb") as f:
                async for chunk in resp.content.iter_chunked(1024*32):
                    f.write(chunk)
    return filename

# ================================
# yt-dlp info + URL سریع
# ================================
def get_info_sync(url):
    with yt_dlp.YoutubeDL(BASE_OPTS) as y:
        info = y.extract_info(url, download=False)
        # مستقیم به URL stream
        url_audio = info['url']
        tid = str(info.get("id"))
        return info, url_audio, tid

# ================================
# هندلر پیام عادی
# ================================
async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.lower()
    triggers = ["آهنگ ", "اهنگ ", "موزیک ", "music "]
    if not any(text.startswith(t) for t in triggers):
        return
    query = next(text[len(t):].strip() for t in triggers if text.startswith(t))
    msg = await update.message.reply_text(TXT["searching"])

    def _search(): 
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            return y.extract_info(f"scsearch10:{query}", download=False)
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(executor, _search)

    if not result or not result.get("entries"):
        return await msg.edit_text(TXT["notfound"])

    entries = {str(t["id"]): t for t in result["entries"]}
    track_store[update.message.message_id] = entries
    keyboard = [
        [InlineKeyboardButton(t["title"][:40], callback_data=f"sel:{update.message.message_id}:{tid}")]
        for tid, t in entries.items()
    ]
    await msg.edit_text(TXT["select"].format(n=len(entries)),
                        reply_markup=InlineKeyboardMarkup(keyboard))

# ================================
# دکمه انتخاب + دانلود موازی
# ================================
async def music_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    _, msg_id, tid = cq.data.split(":")
    msg_id = int(msg_id)
    tracks = track_store.get(msg_id, {})
    track = tracks.get(tid)
    if not track:
        return await cq.edit_message_text("❌ آهنگ پیدا نشد.")

    chat_id = cq.message.chat.id
    cache_key = f"sc_{tid}"
    if cache_key in SC_CACHE:
        return await context.bot.send_audio(chat_id, SC_CACHE[cache_key])

    msg = await cq.edit_message_text(TXT["down"])
    loop = asyncio.get_running_loop()
    info, url, tid = await loop.run_in_executor(executor, get_info_sync, track["webpage_url"])
    file_path = os.path.join(DOWNLOAD_FOLDER, f"{tid}.tmp")

    # دانلود مستقیم با aiohttp
    await download_aio(url, file_path)

    with open(file_path, "rb") as f:
        sent = await context.bot.send_audio(chat_id, f, caption=info.get("title",""))

    os.remove(file_path)
    SC_CACHE[cache_key] = sent.audio.file_id
    save_cache()
    await msg.delete()
