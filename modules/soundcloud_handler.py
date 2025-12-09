# modules/soundcloud_handler.py

import os
import asyncio
import yt_dlp
from concurrent.futures import ThreadPoolExecutor
import json

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InlineQueryResultAudio,
)
from telegram.ext import ContextTypes

# ================================
# سودوها
# ================================

SUDO_USERS = [8588347189]   # ← آیدی شما

# ================================
# تنظیمات
# ================================

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

COOKIE_FILE = "modules/youtube_cookie.txt"

# سرعت بهتر روی سرورهای کم‌قدرت
executor = ThreadPoolExecutor(max_workers=3)

track_store = {}

# ================================
# کش تلگرام فایل‌ها
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
        json.dump(SC_CACHE, f, ensure_ascii=False, indent=2)

# ================================
# پیام‌ها
# ================================

LANG_MESSAGES = {
    "fa": {
        "searching": "🔍 در حال جستجو ...",
        "downloading": "⬇️ در حال دانلود آهنگ...",
        "select_song": "🎵 {n} آهنگ یافت شد — انتخاب کنید:",
        "notfound": "❌ در SoundCloud چیزی نبود. در حال جستجوی یوتیوب...",
    }
}

# ================================
# تنظیمات yt-dlp (سریع و سبک)
# ================================

BASE_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    "noprogress": True,
    "nopart": True,
    "retries": 8,
    "fragment_retries": 8,
    "concurrent_fragment_downloads": 4,  # ← سبکتر
    "overwrites": True,
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "128",
        }
    ],
}

# ================================
# بررسی مدیر بودن
# ================================

async def is_admin(update, context):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private":
        return True
    if user.id in SUDO_USERS:
        return True
    try:
        admins = await context.bot.get_chat_administrators(chat.id)
        ids = [a.user.id for a in admins]
        return user.id in ids
    except:
        return False

# ================================
# کش لوکال mp3
# ================================

def cache_check(id_: str):
    for file in os.listdir(DOWNLOAD_FOLDER):
        if file.startswith(id_) and file.endswith(".mp3"):
            return os.path.join(DOWNLOAD_FOLDER, file)
    return None

# ================================
# دانلود SoundCloud
# ================================

def _sc_download_sync(url: str):
    opts = BASE_OPTS.copy()
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)
        track_id = str(info.get("id"))

        cached = cache_check(track_id)
        if cached:
            return info, cached

        fname = y.prepare_filename(info)
        mp3 = fname.rsplit(".", 1)[0] + ".mp3"
        return info, mp3

# ================================
# fallback یوتیوب
# ================================

def _youtube_fallback_sync(query: str):
    opts = BASE_OPTS.copy()
    if os.path.exists(COOKIE_FILE):
        opts["cookiefile"] = COOKIE_FILE
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(f"ytsearch1:{query}", download=True)
        if "entries" in info:
            info = info["entries"][0]
        vid = str(info.get("id"))
        cached = cache_check(vid)
        if cached:
            return info, cached
        fname = y.prepare_filename(info)
        mp3 = fname.rsplit(".", 1)[0] + ".mp3"
        return info, mp3

# ================================
# جستجو عادی
# ================================

async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    triggers = [
        "آهنگ ", "music ", "اغنية ", "أغنية ",
        "موزیک ", "داستان ", "Music ", "Musik ", "اهنگ "
    ]

    if not any(text.lower().startswith(t) for t in triggers):
        return

    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    lang = "fa"
    query = ""
    for t in triggers:
        if text.lower().startswith(t):
            query = text[len(t):].strip()
            break

    msg = await update.message.reply_text(LANG_MESSAGES[lang]["searching"])

    def _search():
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            return y.extract_info(f"scsearch8:{query}", download=False)

    loop = asyncio.get_running_loop()
    sc_info = await loop.run_in_executor(executor, _search)

    if not sc_info or not sc_info.get("entries"):
        await msg.edit_text(LANG_MESSAGES[lang]["notfound"])
        try:
            info, mp3 = await loop.run_in_executor(executor, _youtube_fallback_sync, query)
        except Exception as e:
            return await msg.edit_text(f"❌ خطای یوتیوب:\n{e}")

        yt_id = f"yt_{info.get('id')}"

        if yt_id in SC_CACHE:
            await msg.delete()
            return await update.message.reply_audio(
                SC_CACHE[yt_id],
                caption=f"🎵 {info.get('title')}\n📥 دانلود موزیک",
                parse_mode="HTML"
            )

        with open(mp3, "rb") as f:
            sent = await update.message.reply_audio(
                f,
                caption=f"🎵 {info.get('title')}\n📥 دانلود موزیک",
                parse_mode="HTML"
            )

        SC_CACHE[yt_id] = sent.audio.file_id
        save_cache()

        await msg.delete()
        return

    entries = sc_info["entries"]
    track_store[update.effective_chat.id] = entries

    keyboard = [[InlineKeyboardButton(t["title"], callback_data=f"music_select:{t['id']}")] for t in entries]

    await msg.edit_text(
        LANG_MESSAGES[lang]["select_song"].format(n=len(entries)),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================================
# دانلود انتخاب‌شده
# ================================

async def music_select_handler(update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()

    chat = cq.message.chat_id

    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    track_id = cq.data.split(":")[1]
    cache_key = f"sc_{track_id}"

    if cache_key in SC_CACHE:
        return await context.bot.send_audio(chat, SC_CACHE[cache_key])

    tracks = track_store.get(chat, [])
    track = next((t for t in tracks if str(t["id"]) == track_id), None)

    if not track:
        return await cq.edit_message_text("❌ آهنگ یافت نشد.")

    msg = await cq.edit_message_text("⬇️ در حال دانلود...")
    loop = asyncio.get_running_loop()

    try:
        info, mp3 = await loop.run_in_executor(executor, _sc_download_sync, track["webpage_url"])
    except Exception as e:
        return await msg.edit_text(f"❌ خطا:\n{e}")

    with open(mp3, "rb") as f:
        sent = await context.bot.send_audio(
            chat,
            f,
            caption=f"🎵 {info.get('title')}\n📥 دانلود موزیک",
            parse_mode="HTML"
        )

    SC_CACHE[cache_key] = sent.audio.file_id
    save_cache()

    await msg.delete()

# ================================
# ================================
#     INLINE MODE (درون‌خطی)
# ================================
# ================================

async def inline_sc(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.inline_query.query.strip()

    if len(q) < 2:
        return

    def _search():
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            return y.extract_info(f"scsearch5:{q}", download=False)

    loop = asyncio.get_running_loop()
    sc_info = await loop.run_in_executor(executor, _search)

    results = []

    if sc_info and sc_info.get("entries"):
        for t in sc_info["entries"]:
            results.append(
                InlineQueryResultAudio(
                    id=str(t["id"]),
                    title=t["title"],
                    audio_url=t["url"],
                )
            )

    await update.inline_query.answer(results, cache_time=1)
