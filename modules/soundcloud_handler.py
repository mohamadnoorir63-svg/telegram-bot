# ================================
# modules/soundcloud_handler.py
# نسخه کامل با کش تلگرامی (file_id cache)
# ================================

import os
import json
import asyncio
import yt_dlp
from concurrent.futures import ThreadPoolExecutor

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# ================================
# تنظیمات
# ================================
SUDO_USERS = [8588347189]
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

COOKIE_FILE = "modules/youtube_cookie.txt"

executor = ThreadPoolExecutor(max_workers=8)

track_store = {}

CACHE_FILE = "data/soundcloud_cache.json"
os.makedirs("data", exist_ok=True)

# اگر فایل کش موجود نبود → بساز
if not os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "w") as fp:
        json.dump({}, fp)

# لود کش
with open(CACHE_FILE, "r") as fp:
    SC_CACHE = json.load(fp)


def save_cache():
    with open(CACHE_FILE, "w") as fp:
        json.dump(SC_CACHE, fp, indent=2)


# ================================
# پیام‌ها
# ================================
LANG_MESSAGES = {
    "fa": {
        "searching": "🔍 در حال جستجو ... لطفاً صبر کنید",
        "downloading": "⬇️ در حال دانلود آهنگ...",
        "select_song": "🎵 {n} آهنگ پیدا شد — لطفاً انتخاب کنید:",
        "notfound": "❌ در SoundCloud چیزی پیدا نشد. در حال جستجو در یوتیوب...",
    }
}


# ================================
# چک مدیر
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
        return user.id in [a.user.id for a in admins]
    except:
        return False


# ================================
# دانلود SoundCloud (با تبدیل mp3)
# ================================
def _sc_download_sync(url: str):
    opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    }

    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)

        track_id = str(info.get("id"))
        fname = y.prepare_filename(info)
        mp3 = fname.rsplit(".", 1)[0] + ".mp3"

        return info, mp3


# ================================
# fallback یوتیوب
# ================================
def _youtube_fallback_sync(query: str):
    opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    }

    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(f"ytsearch1:{query}", download=True)

        if "entries" in info:
            info = info["entries"][0]

        fname = y.prepare_filename(info)
        mp3 = fname.rsplit(".", 1)[0] + ".mp3"

        return info, mp3


# ================================
# مرحله اول: جستجو
# ================================
async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    txt = update.message.text.strip()

    triggers = ["آهنگ ", "music ", "اغنية ", "أغنية "]
    if not any(txt.lower().startswith(t) for t in triggers):
        return

    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    # استخراج query
    for t in triggers:
        if txt.lower().startswith(t):
            query = txt[len(t):].strip()
            break

    msg = await update.message.reply_text("🔍 در حال جستجو ...")

    def _search():
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            return y.extract_info(f"scsearch3:{query}", download=False)

    loop = asyncio.get_running_loop()
    sc_info = await loop.run_in_executor(executor, _search)

    if not sc_info or not sc_info.get("entries"):
        await msg.edit_text("❌ در SoundCloud چیزی پیدا نشد. در حال جستجو در یوتیوب...")

        info, mp3 = await loop.run_in_executor(executor, _youtube_fallback_sync, query)

        sent = await update.message.reply_audio(
            audio=open(mp3, "rb"),
            caption=f"🎵 {info['title']}"
        )

        # ذخیره در کش
        track_id = str(info["id"])
        SC_CACHE[track_id] = sent.audio.file_id
        save_cache()

        os.remove(mp3)
        return

    # ساخت دکمه انتخاب
    entries = sc_info["entries"]
    track_store[update.effective_chat.id] = entries

    keyboard = [
        [InlineKeyboardButton(t["title"], callback_data=f"music:{t['id']}")]
        for t in entries
    ]

    await msg.edit_text(
        f"🎵 {len(entries)} آهنگ پیدا شد — انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================================
# مرحله دوم: دانلود انتخاب شده
# ================================
async def music_select_handler(update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()

    chat = cq.message.chat_id

    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    track_id = cq.data.split(":")[1]

    # اگر قبلاً در کش داریم → مستقیم فایل ID را بفرست
    if track_id in SC_CACHE:
        await cq.edit_message_text("⚡ ارسال سریع از کش...")
        return await context.bot.send_audio(chat, SC_CACHE[track_id])

    # پیدا کردن ترک
    tracks = track_store.get(chat, [])
    track = next((t for t in tracks if str(t["id"]) == track_id), None)

    if not track:
        return await cq.edit_message_text("❌ آهنگ پیدا نشد.")

    await cq.edit_message_text("⬇️ در حال دانلود ...")

    loop = asyncio.get_running_loop()
    info, mp3_path = await loop.run_in_executor(
        executor, _sc_download_sync, track["webpage_url"]
    )

    sent = await context.bot.send_audio(chat, open(mp3_path, "rb"), caption=f"🎵 {info['title']}")

    # ذخیره file_id در کش
    SC_CACHE[track_id] = sent.audio.file_id
    save_cache()

    os.remove(mp3_path)
