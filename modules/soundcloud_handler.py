# modules/soundcloud_handler.py

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

# ThreadPoolExecutor (Heroku-safe — کم‌هسته)
executor = ThreadPoolExecutor(max_workers=3)

# کش نتایج جستجو (برای دکمه‌ها)
track_store = {}

# ================================
# کش تلگرام (file_id)
# ================================
CACHE_FILE = "data/sc_cache.json"
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
        "searching": "🔍",
        "downloading": "⌛",
        "select_song": "🎵 {n} آهنگ پیدا شد — لطفاً انتخاب کنید:",
        "notfound": "⌛",
    }
}

# ================================
# تنظیمات yt_dlp (بهینه)
# ================================
BASE_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    "noprogress": True,
    "nopart": True,
    "retries": 8,
    "fragment_retries": 8,
    "concurrent_fragment_downloads": 4,
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
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private":
        return True
    if user and user.id in SUDO_USERS:
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
def cache_check(id_: str) -> Optional[str]:
    for file in os.listdir(DOWNLOAD_FOLDER):
        if file.startswith(id_) and file.endswith(".mp3"):
            return os.path.join(DOWNLOAD_FOLDER, file)
    return None

# ================================
# دانلود SoundCloud (blocking)
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
# دانلود fallback یوتیوب (blocking)
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
# هندلر پیام (جستجوی عادی با triggers)
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

    query = ""
    for t in triggers:
        if text.lower().startswith(t):
            query = text[len(t):].strip()
            break

    msg = await update.message.reply_text(LANG_MESSAGES["fa"]["searching"])

    def _search():
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            return y.extract_info(f"scsearch8:{query}", download=False)

    loop = asyncio.get_running_loop()
    try:
        sc_info = await loop.run_in_executor(executor, _search)
    except Exception as e:
        await msg.edit_text(f"❌ خطا در جستجو:\n{e}")
        return

    if not sc_info or not sc_info.get("entries"):
        await msg.edit_text(LANG_MESSAGES["fa"]["notfound"])
        try:
            info, mp3 = await loop.run_in_executor(executor, _youtube_fallback_sync, query)
        except Exception as e:
            return await msg.edit_text(f"❌ خطا در جستجوی یوتیوب:\n{e}")

        yt_id = f"yt_{info.get('id')}"
        if yt_id in SC_CACHE:
            try:
                await msg.delete()
            except Exception:
                pass
            return await update.message.reply_audio(
                SC_CACHE[yt_id],
                caption=f"🎵 {info.get('title', 'Music')}\n\n📥 <a href='https://t.me/AFGR63_bot'>دانلود موزیک</a>",
                parse_mode="HTML",
            )

        try:
            with open(mp3, "rb") as f:
                keyboard = [[InlineKeyboardButton(
                    "➕ افزودن به گروه",
                    url="https://t.me/AFGR63_bot?startgroup=true"
                )]] if update.effective_chat.type == "private" else None

                sent = await update.message.reply_audio(
                    f,
                    caption=f"🎵 {info.get('title', 'Music')}\n\n📥 <a href='https://t.me/AFGR63_bot'>دانلود موزیک</a>",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
                )
        except Exception as e:
            return await msg.edit_text(f"❌ خطا در ارسال فایل:\n{e}")
        finally:
            if os.path.exists(mp3):
                os.remove(mp3)

        SC_CACHE[yt_id] = sent.audio.file_id
        save_cache()
        try:
            await msg.delete()
        except Exception:
            pass
        return

    # سریع و امن برای چند کاربر
    store_key = f"{update.effective_chat.id}_{update.message.message_id}"
    entries = {str(t["id"]): t for t in sc_info["entries"]}
    track_store[store_key] = entries

    keyboard = [
        [InlineKeyboardButton(t["title"], callback_data=f"music_select:{store_key}:{t_id}")]
        for t_id, t in entries.items()
    ]

    await msg.edit_text(
        LANG_MESSAGES["fa"]["select_song"].format(n=len(entries)),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# ================================
# دانلود انتخاب‌شده (callback)
# ================================
async def music_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    chat_id = cq.message.chat.id

    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    try:
        _, store_key, track_id = cq.data.split(":")
    except ValueError:
        return await cq.edit_message_text("❌ خطا در callback.")

    tracks = track_store.get(store_key, {})
    track = tracks.get(track_id)
    if not track:
        return await cq.edit_message_text("❌ آهنگ پیدا نشد.")

    cache_key = f"sc_{track_id}"
    if cache_key in SC_CACHE:
        try:
            await cq.edit_message_text("⚡ در حال ارسال از کش تلگرام...")
        except Exception:
            pass
        return await context.bot.send_audio(chat_id, SC_CACHE[cache_key])

    msg = await cq.edit_message_text(LANG_MESSAGES["fa"]["downloading"])
    loop = asyncio.get_running_loop()

    try:
        info, mp3 = await loop.run_in_executor(executor, _sc_download_sync, track["webpage_url"])
    except Exception as e:
        return await msg.edit_text(f"❌ خطا در دانلود:\n{e}")

    try:
        with open(mp3, "rb") as f:
            keyboard = [[InlineKeyboardButton(
                "➕ افزودن به گروه",
                url="https://t.me/AFGR63_bot?startgroup=true"
            )]] if update.effective_chat.type == "private" else None

            sent = await context.bot.send_audio(
                chat_id,
                f,
                caption=f"🎵 {info.get('title', 'Music')}\n\n📥 <a href='https://t.me/AFGR63_bot'>دانلود موزیک</a>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
            )
    except Exception as e:
        return await msg.edit_text(f"❌ خطا در ارسال فایل:\n{e}")
    finally:
        if os.path.exists(mp3):
            try:
                os.remove(mp3)
            except Exception:
                pass

    SC_CACHE[cache_key] = sent.audio.file_id
    save_cache()
    try:
        await msg.delete()
    except Exception:
        pass
