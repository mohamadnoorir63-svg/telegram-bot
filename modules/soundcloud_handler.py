# modules/soundcloud_handler.py

import os
import asyncio
import yt_dlp
from concurrent.futures import ThreadPoolExecutor
import json

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# ================================
# سودوها
# ================================
SUDO_USERS = [8588347189]  # ← آیدی شما

# ================================
# تنظیمات
# ================================
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

COOKIE_FILE = "modules/youtube_cookie.txt"
executor = ThreadPoolExecutor(max_workers=8)

# کش ترک‌ها در حافظه (نتایج جستجو برای انتخاب دکمه)
track_store = {}
LYRICS_STORE = {}  # کش متن موزیک

# ================================
# کش تلگرام (file_id)
# ================================
CACHE_FILE = "data/custom_commands.json"
os.makedirs("data", exist_ok=True)

if not os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

with open(CACHE_FILE, "r", encoding="utf-8") as f:
    try:
        SC_CACHE = json.load(f)
    except json.JSONDecodeError:
        SC_CACHE = {}

def save_cache():
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(SC_CACHE, f, ensure_ascii=False, indent=2)

# ================================
# پیام‌ها
# ================================
LANG_MESSAGES = {
    "fa": {
        "searching": "🔍 در حال جستجو ... لطفاً صبر کنید",
        "downloading": "⬇️ در حال دانلود آهنگ...",
        "select_song": "🎵 {n} آهنگ پیدا شد — لطفاً انتخاب کنید:",
        "notfound": "❌ در SoundCloud چیزی پیدا نشد. در حال جستجو در یوتیوب...",
    },
    "en": {
        "searching": "🔍 Searching... please wait",
        "downloading": "⬇️ Downloading...",
        "select_song": "🎵 {n} songs found — choose one:",
        "notfound": "❌ No results in SoundCloud. Searching YouTube...",
    },
}

# ================================
# تنظیمات yt_dlp
# ================================
BASE_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    "noprogress": True,
    "nopart": True,
    "retries": 20,
    "fragment_retries": 20,
    "concurrent_fragment_downloads": 20,
    "overwrites": True,
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
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
    except Exception:
        return False

# ================================
# چک کش mp3 لوکال
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
# دانلود fallback یوتیوب
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
# handler اصلی
# ================================
async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    triggers = ["آهنگ ", "music ", "اغنية ", "أغنية ", "داستان", "موزیک", "خبر"]
    if not any(text.lower().startswith(t) for t in triggers):
        return
    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    # تعیین query
    lang = "fa"
    query = ""
    for t in triggers:
        if text.lower().startswith(t):
            query = text[len(t):].strip()
            lang = "en" if t.startswith("music") else ("fa" if "غ" not in t else "ar")
            break

    msg = await update.message.reply_text(LANG_MESSAGES[lang]["searching"])

    def _search():
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            return y.extract_info(f"scsearch7:{query}", download=False)

    loop = asyncio.get_running_loop()
    sc_info = await loop.run_in_executor(executor, _search)

    if not sc_info or not sc_info.get("entries"):
        await msg.edit_text(LANG_MESSAGES[lang]["notfound"])
        try:
            info, mp3 = await loop.run_in_executor(executor, _youtube_fallback_sync, query)
        except Exception as e:
            return await msg.edit_text(f"❌ خطا در جستجوی یوتیوب:\n{e}")

        yt_id = str(info.get("id"))
        cache_key = f"yt_{yt_id}"
        if cache_key in SC_CACHE:
            try: await msg.delete()
            except: pass
            return await update.message.reply_audio(SC_CACHE[cache_key], caption=f"🎵 {info.get('title','Music')}")

        try:
            with open(mp3, "rb") as f:
                sent = await update.message.reply_audio(f, caption=f"🎵 {info.get('title','Music')}")
        except Exception as e:
            return await msg.edit_text(f"❌ خطا در ارسال فایل:\n{e}")
        finally:
            if os.path.exists(mp3): os.remove(mp3)

        SC_CACHE[cache_key] = sent.audio.file_id
        save_cache()
        try: await msg.delete()
        except: pass
        return

    entries = sc_info["entries"]
    track_store[update.effective_chat.id] = entries

    keyboard = [[InlineKeyboardButton(t["title"], callback_data=f"music_select:{t['id']}")] for t in entries]

    await msg.edit_text(LANG_MESSAGES[lang]["select_song"].format(n=len(entries)), reply_markup=InlineKeyboardMarkup(keyboard))

# ================================
# انتخاب موزیک
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
        try: await cq.edit_message_text("⚡ در حال ارسال از کش تلگرام...")
        except: pass
        return await context.bot.send_audio(chat, SC_CACHE[cache_key])

    tracks = track_store.get(chat, [])
    track = next((t for t in tracks if str(t["id"]) == track_id), None)
    if not track:
        return await cq.edit_message_text("❌ آهنگ پیدا نشد.")

    msg = await cq.edit_message_text("⬇️ در حال دانلود...")
    loop = asyncio.get_running_loop()
    try:
        info, mp3 = await loop.run_in_executor(executor, _sc_download_sync, track["webpage_url"])
    except Exception as e:
        return await msg.edit_text(f"❌ خطا در دانلود:\n{e}")

    try:
        # ارسال آهنگ + دکمه نمایش متن
        keyboard = [[InlineKeyboardButton("🎵 دانلود موزیک", callback_data=f"show_lyrics:{track_id}")]]
        with open(mp3, "rb") as f:
            sent = await context.bot.send_audio(chat, f, caption=f"🎵 {info.get('title','Music')}", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        return await msg.edit_text(f"❌ خطا در ارسال فایل:\n{e}")
    finally:
        if os.path.exists(mp3): os.remove(mp3)

    SC_CACHE[cache_key] = sent.audio.file_id
    LYRICS_STORE[track_id] = track.get("description", "❌ متن موزیک موجود نیست.")  # ذخیره متن موزیک
    save_cache()
    try: await msg.delete()
    except: pass

# ================================
# نمایش متن موزیک
# ================================
async def show_lyrics_handler(update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    track_id = cq.data.split(":")[1]
    lyrics = LYRICS_STORE.get(track_id, "❌ متن موزیک موجود نیست.")
    await cq.edit_message_text(f"🎵 متن موزیک:\n\n{lyrics}")
