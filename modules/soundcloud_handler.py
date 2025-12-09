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
    InlineQueryResultArticle,
    InputTextMessageContent,
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
# ================================
# ارسال موزیک از حافظه‌ی کش (همانند دانلود مستقیم)
# ================================
async def send_from_cache(chat_id, track_id, bot, context):
    try:
        cache_entry = SC_CACHE.get(track_id)
        if not cache_entry:
            return False

        file_path = cache_entry["file"]

        if not os.path.exists(file_path):
            # فایل پاک شده → کش را ریست می‌کنیم
            del SC_CACHE[track_id]
            save_cache()
            return False

        keyboard = [[InlineKeyboardButton(
            "➕ افزودن به گروه",
            url="https://t.me/AFGR63_bot?startgroup=true"
        )]]

        caption = f"🎵 {cache_entry.get('title', 'Music')}\n\n📥 <a href='https://t.me/AFGR63_bot'>دانلود موزیک</a>"

        with open(file_path, "rb") as f:
            await bot.send_audio(
                chat_id,
                f,
                caption=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        return True

    except Exception as e:
        print("Cache send error:", e)
        return False

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
            "preferredquality": "128",  # سبک‌تر و سریع‌تر
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
        # اگر قبلاً در کش لوکال داریم → همان را بده
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

    # گروه → فقط مدیر
    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    # تعیین query
    query = ""
    for t in triggers:
        if text.lower().startswith(t):
            query = text[len(t):].strip()
            break

    msg = await update.message.reply_text(LANG_MESSAGES["fa"]["searching"])

    # جستجوی سریع در SoundCloud (blocking) داخل executor
    def _search():
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            return y.extract_info(f"scsearch8:{query}", download=False)

    loop = asyncio.get_running_loop()
    try:
        sc_info = await loop.run_in_executor(executor, _search)
    except Exception as e:
        await msg.edit_text(f"❌ خطا در جستجو:\n{e}")
        return

    # اگر نتیجه نداشت → fallback یوتیوب
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
                keyboard = None
                if update.effective_chat.type == "private":
                    keyboard = [[InlineKeyboardButton(
                        "➕ افزودن به گروه",
                        url="https://t.me/AFGR63_bot?startgroup=true"
                    )]]

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

    # ساخت لیست انتخاب از نتایج SoundCloud
    entries = sc_info["entries"]
    track_store[update.effective_chat.id] = entries

    keyboard = [
        [InlineKeyboardButton(t["title"], callback_data=f"music_select:{t['id']}")]
        for t in entries
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

    chat_id = cq.message.chat.id  # ← مطمئن شوید همیشه chat_id درست است

    # گروه → فقط مدیر
    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    track_id = cq.data.split(":")[1]
    cache_key = f"sc_{track_id}"

    # اگر از قبل کش شده در تلگرام باشد
    if cache_key in SC_CACHE:
        try:
            await cq.edit_message_text("⚡ در حال ارسال از کش تلگرام...")
        except Exception:
            pass
        return await context.bot.send_audio(chat_id, SC_CACHE[cache_key])

    # استفاده از chat_id درست
    tracks = track_store.get(chat_id, [])
    track = next((t for t in tracks if str(t["id"]) == track_id), None)

    if not track:
        return await cq.edit_message_text("❌ آهنگ پیدا نشد.")

    msg = await cq.edit_message_text(LANG_MESSAGES["fa"]["downloading"])
    loop = asyncio.get_running_loop()

    try:
        info, mp3 = await loop.run_in_executor(executor, _sc_download_sync, track["webpage_url"])
    except Exception as e:
        return await msg.edit_text(f"❌ خطا در دانلود:\n{e}")

    try:
        with open(mp3, "rb") as f:
            keyboard = None
            if update.effective_chat.type == "private":
                keyboard = [[InlineKeyboardButton(
                    "➕ افزودن به گروه",
                    url="https://t.me/AFGR63_bot?startgroup=true"
                )]]

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
