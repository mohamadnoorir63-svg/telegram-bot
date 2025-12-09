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
# SUDO
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
# متن‌ها
# ================================
TXT = {
    "searching": "🔍 در حال جستجو...",
    "down": "⏳ آماده‌سازی دانلود...",
    "notfound": "❌ نتیجه‌ای یافت نشد.",
}

# ================================
# ThreadPool سریع
# ================================
executor = ThreadPoolExecutor(max_workers=12)   # افزایش سرعت


# ================================
# yt_dlp آپشن‌های نهایی — سریع‌ترین حالت
# ================================
BASE_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "noprogress": True,
    "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    "retries": 10,
    "fragment_retries": 10,
    "concurrent_fragment_downloads": 16,  # سرعت بیشتر
    "nopart": True,
    "overwrites": True,
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "128",
        }
    ],
}

track_store = {}

# ================================
# بررسی کش فایل
# ================================
def cache_check(id_: str):
    for f in os.listdir(DOWNLOAD_FOLDER):
        if f.startswith(id_) and f.endswith(".mp3"):
            return os.path.join(DOWNLOAD_FOLDER, f)
    return None


# ================================
# دانلود SoundCloud
# ================================
def _download_sc(url: str):
    opts = BASE_OPTS.copy()
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)

        tid = str(info.get("id"))

        cache_file = cache_check(tid)
        if cache_file:
            return info, cache_file

        fname = y.prepare_filename(info)
        mp3 = fname.rsplit(".", 1)[0] + ".mp3"
        return info, mp3


# ================================
# کنترل پیام‌های عادی
# ================================
async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    triggers = ["آهنگ ", "اهنگ ", "موزیک ", "music "]
    if not any(text.lower().startswith(t) for t in triggers):
        return

    # استخراج نام آهنگ
    query = next(
        text[len(t):].strip()
        for t in triggers
        if text.lower().startswith(t)
    )

    msg = await update.message.reply_text(TXT["searching"])

    def _search():
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            return y.extract_info(f"scsearch15:{query}", download=False)

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(executor, _search)

    if not result or not result.get("entries"):
        return await msg.edit_text(TXT["notfound"])

    entries = {str(t["id"]): t for t in result["entries"]}

    track_store[update.message.message_id] = entries

    keyboard = [
        [
            InlineKeyboardButton(
                t["title"][:40],  # جلوگیری از طول زیاد
                callback_data=f"music_select:{update.message.message_id}:{tid}"
            )
        ]
        for tid, t in entries.items()
    ]

    await msg.edit_text(
        f"🎵 {len(entries)} نتیجه یافت شد — انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================================
# دانلود از دکمه معمولی
# ================================
async def music_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()

    _, msg_id, tid = cq.data.split(":")
    msg_id = int(msg_id)

    track = track_store.get(msg_id, {}).get(tid)
    if not track:
        return await cq.edit_message_text("❌ آهنگ یافت نشد.")

    chat_id = cq.message.chat.id
    cache_key = f"sc_{tid}"

    # کش تلگرام
    if cache_key in SC_CACHE:
        return await context.bot.send_audio(chat_id, SC_CACHE[cache_key])

    # پیام لودینگ
    msg = await cq.edit_message_text(TXT["down"])

    loop = asyncio.get_running_loop()
    info, mp3 = await loop.run_in_executor(executor, _download_sc, track["webpage_url"])

    with open(mp3, "rb") as f:
        sent = await context.bot.send_audio(chat_id, f, caption=info.get("title", ""))

    os.remove(mp3)
    SC_CACHE[cache_key] = sent.audio.file_id
    save_cache()

    await msg.delete()


# ================================
# جستجوی Inline (فوق سریع)
# ================================
async def inline_sc(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.inline_query.query.strip()
    if not query:
        return

    def _search():
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            return y.extract_info(f"scsearch12:{query}", download=False)

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(executor, _search)

    results = []

    for t in result.get("entries", [])[:8]:
        tid = str(t["id"])
        track_store[f"inline_{tid}"] = t

        results.append(
            InlineQueryResultArticle(
                id=tid,
                title=t["title"],
                description="دانلود سریع",
                input_message_content=InputTextMessageContent(
                    f"🎵 {t['title']}\n⏳ در حال دانلود..."
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬇ دانلود", callback_data=f"music_inline:{tid}")]
                ])
            )
        )

    await update.inline_query.answer(results, cache_time=0)


# ================================
# دانلود دکمه inline
# ================================
async def music_inline_handler(update, context):
    cq = update.callback_query
    await cq.answer()

    tid = cq.data.split(":")[1]
    track = track_store.get(f"inline_{tid}")

    if not track:
        return await cq.edit_message_text("❌ آهنگ یافت نشد.")

    msg = await cq.edit_message_text("⏳ دانلود...")

    loop = asyncio.get_running_loop()
    info, mp3 = await loop.run_in_executor(executor, _download_sc, track["webpage_url"])

    with open(mp3, "rb") as f:
        sent = await context.bot.send_audio(cq.message.chat.id, f, caption=info.get("title", ""))

    os.remove(mp3)

    await msg.delete()
