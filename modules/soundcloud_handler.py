import os
import asyncio
import yt_dlp
import json
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, COMM
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes


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
# متن‌های ربات
# ================================
TXT = {
    "searching": "🔎 در حال جستجو...",
    "select": "🎵 {n} نتیجه یافت شد — انتخاب کنید:",
    "down": "⏳ دانلود...",
    "notfound": "⚠ نتیجه‌ای پیدا نشد!",
}


# ================================
# تنظیمات yt_dlp اصلی
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
# بررسی وجود فایل mp3 در کش محلی
# ================================
def cache_check(id_: str) -> Optional[str]:
    for file in os.listdir(DOWNLOAD_FOLDER):
        if file.startswith(id_) and file.endswith(".mp3"):
            return os.path.join(DOWNLOAD_FOLDER, file)
    return None


# ================================
# واترمارک داخل MP3
# ================================
def add_watermark(mp3_path, title="Music", artist="Unknown"):
    wm = "دانلود شده با بهترین کیفیت\nhttps://t.me/AFGR63_bot"

    try:
        audio = EasyID3(mp3_path)
    except:
        audio = ID3()

    audio["title"] = title
    audio["artist"] = artist
    audio["album"] = title
    audio.save(mp3_path)

    id3 = ID3(mp3_path)
    id3.add(COMM(encoding=3, lang="eng", desc="Comment", text=wm))
    id3.save(mp3_path)


# ================================
# fallback YouTube بسیار سریع
# ================================
def youtube_fallback_sync(query: str):
    opts = BASE_OPTS.copy()
    opts.update({
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }
        ],
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
        "concurrent_fragment_downloads": 20
    })

    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(f"ytsearch1:{query}", download=True)
        if "entries" in info:
            info = info["entries"][0]

        vid = info["id"]
        mp3_path = f"{DOWNLOAD_FOLDER}/{vid}.mp3"

    add_watermark(mp3_path, info.get("title"), info.get("uploader"))
    return info, mp3_path


async def youtube_fallback(query: str):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, youtube_fallback_sync, query)


# ================================
# دانلود SoundCloud
# ================================
def sc_download_sync(url: str):
    opts = BASE_OPTS.copy()
    opts["postprocessors"] = []

    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)
        tid = info["id"]

        cached = cache_check(tid)
        if cached:
            return info, cached

        fname = y.prepare_filename(info)
        return info, fname


async def sc_download(url: str):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, sc_download_sync, url)


# ================================
# هندلر پیام اصلی
# ================================
async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()
    triggers = ["آهنگ ", "music ", "اهنگ ", "موزیک "]

    if not any(text.startswith(t) for t in triggers):
        return

    query = next((update.message.text[len(t):].strip() for t in triggers if text.startswith(t)), "")
    msg = await update.message.reply_text(TXT["searching"])

    # جستجوی SoundCloud
    loop = asyncio.get_running_loop()

    def _search_sc():
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            return y.extract_info(f"scsearch10:{query}", download=False)

    try:
        result = await loop.run_in_executor(executor, _search_sc)
    except:
        result = None

    # اگر SoundCloud نتیجه نداد → YouTube
    if not result or not result.get("entries"):
        await msg.edit_text("نتیجه‌ای پیدا نشد! در حال جستجو در YouTube…")

        info, mp3 = await youtube_fallback(query)

        cache_key = f"yt_{info.get('id')}"
        with open(mp3, "rb") as f:
            sent = await update.message.reply_audio(f, caption=info.get("title", "Music"))

        SC_CACHE[cache_key] = sent.audio.file_id
        save_cache()
        await msg.delete()
        return

    # SoundCloud → نمایش دکمه‌ها
    entries = {str(t["id"]): t for t in result["entries"]}
    track_store[update.message.message_id] = entries

    keyboard = [
        [InlineKeyboardButton(t["title"], callback_data=f"music_select:{update.message.message_id}:{tid}")]
        for tid, t in entries.items()
    ]

    await msg.edit_text(TXT["select"].format(n=len(entries)), reply_markup=InlineKeyboardMarkup(keyboard))


# ================================
# هندلر انتخاب آهنگ
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

    # ارسال از کش تلگرام
    if cache_key in SC_CACHE:
        return await context.bot.send_audio(chat_id, SC_CACHE[cache_key])

    msg = await cq.edit_message_text(TXT["down"])

    info, mp3 = await sc_download(track["webpage_url"])

    add_watermark(mp3, info.get("title"), info.get("uploader"))

    with open(mp3, "rb") as f:
        sent = await context.bot.send_audio(
            chat_id,
            f,
            caption=info.get("title", "")
        )

    SC_CACHE[cache_key] = sent.audio.file_id
    save_cache()

    os.remove(mp3)
    await msg.delete()
