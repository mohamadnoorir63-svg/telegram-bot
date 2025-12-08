# ================================
# modules/soundcloud_handler.py
# ================================

import os
import asyncio
import yt_dlp
from concurrent.futures import ThreadPoolExecutor
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import json

# ================================
# سودوها
# ================================
SUDO_USERS = [8588347189]

# ================================
# تنظیمات
# ================================
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

COOKIE_FILE = "modules/youtube_cookie.txt"

executor = ThreadPoolExecutor(max_workers=8)

track_store = {}

# 🔥 کش جدید تلگرام برای SoundCloud
CACHE_FILE = "data/soundcloud_cache.json"
os.makedirs("data", exist_ok=True)

if not os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "w") as f:
        json.dump({}, f)

with open(CACHE_FILE, "r") as f:
    SC_CACHE = json.load(f)

def save_cache():
    with open(CACHE_FILE, "w") as f:
        json.dump(SC_CACHE, f, indent=4)


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
# تنظیمات Turbo yt_dlp
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
        {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
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
# چک کش mp3 (فایل فیزیکی)
# ================================
def cache_check(id_: str):
    for file in os.listdir(DOWNLOAD_FOLDER):
        if file.startswith(id_) and file.endswith(".mp3"):
            return os.path.join(DOWNLOAD_FOLDER, file)
    return None

# ================================
# دانلود SoundCloud + Cache
# ================================
def _sc_download_sync(url: str):
    opts = BASE_OPTS.copy()

    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)

        track_id = str(info.get("id"))

        # فایل خروجی
        fname = y.prepare_filename(info)
        mp3 = fname.rsplit(".", 1)[0] + ".mp3"

        return info, track_id, mp3

# ================================
# جستجو و ساخت لیست انتخاب
# ================================
async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    triggers = ["آهنگ ", "music ", "اغنية ", "أغنية "]

    if not any(text.lower().startswith(t) for t in triggers):
        return

    # فقط مدیر در گروه
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
            return y.extract_info(f"scsearch3:{query}", download=False)

    loop = asyncio.get_running_loop()
    sc_info = await loop.run_in_executor(executor, _search)

    if not sc_info or not sc_info.get("entries"):
        return await msg.edit_text(LANG_MESSAGES[lang]["notfound"])

    entries = sc_info["entries"]
    track_store[update.effective_chat.id] = entries

    keyboard = [
        [InlineKeyboardButton(t["title"], callback_data=f"music_select:{t['id']}")]
        for t in entries
    ]

    await msg.edit_text(
        LANG_MESSAGES[lang]["select_song"].format(n=len(entries)),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# ================================
# دانلود انتخاب‌شده + کش تلگرام
# ================================
async def music_select_handler(update, context: ContextTypes.DEFAULT_TYPE):

    cq = update.callback_query
    await cq.answer()

    chat = cq.message.chat_id

    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    track_id = cq.data.split(":")[1]

    # 🎯 اگر قبلاً در تلگرام ذخیره شده → سریع ارسال کن
    if track_id in SC_CACHE:
        file_id = SC_CACHE[track_id]["file_id"]
        await context.bot.send_audio(chat, file_id)
        return await cq.edit_message_text("⚡ ارسال سریع از کش تلگرام!")

    tracks = track_store.get(chat, [])
    track = next((t for t in tracks if str(t["id"]) == track_id), None)

    if not track:
        return await cq.edit_message_text("❌ آهنگ پیدا نشد.")

    msg = await cq.edit_message_text("⬇️ در حال دانلود...")

    loop = asyncio.get_running_loop()
    info, tid, mp3 = await loop.run_in_executor(
        executor, _sc_download_sync, track["webpage_url"]
    )

    sent = await context.bot.send_audio(chat, open(mp3, "rb"), caption=f"🎵 {info['title']}")

    # 🟩 ذخیره file_id در کش
    SC_CACHE[tid] = {"file_id": sent.audio.file_id}
    save_cache()

    await msg.delete()
