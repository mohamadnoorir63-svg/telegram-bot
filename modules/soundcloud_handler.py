# ================================
# SoundCloud Handler — With Telegram Cache
# ================================

import os
import json
import asyncio
import yt_dlp
import subprocess
from concurrent.futures import ThreadPoolExecutor
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# ================================
# سودو
# ================================
SUDO_USERS = [8588347189]

# ================================
# مسیرها
# ================================
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

CACHE_FILE = "data/sound_cache.json"
os.makedirs("data", exist_ok=True)

# اگر کش وجود ندارد بسازیم
if not os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "w") as f:
        json.dump({}, f)

with open(CACHE_FILE, "r") as f:
    SC_CACHE = json.load(f)

def save_cache():
    with open(CACHE_FILE, "w") as f:
        json.dump(SC_CACHE, f, indent=4)

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
    "concurrent_fragment_downloads": 20,  # سرعت بالا
    "overwrites": True,
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
}

executor = ThreadPoolExecutor(max_workers=8)
track_store = {}

LANG_MESSAGES = {
    "fa": {
        "searching": "🔍 در حال جستجو ... لطفاً صبر کنید",
        "downloading": "⬇️ در حال دانلود آهنگ...",
        "select_song": "🎵 {n} آهنگ پیدا شد — لطفاً انتخاب کنید:",
        "notfound": "❌ در SoundCloud چیزی پیدا نشد. در حال جستجو در یوتیوب...",
    }
}

# ================================
# چک مدیر بودن
# ================================
async def is_admin(update, context):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == "private": return True
    if user.id in SUDO_USERS: return True

    try:
        admins = await context.bot.get_chat_administrators(chat.id)
        return user.id in [a.user.id for a in admins]
    except:
        return False


# ================================
# دانلود SoundCloud با Turbo + Cache
# ================================
def _sc_download_sync(url):
    opts = BASE_OPTS.copy()

    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)
        track_id = str(info["id"])

        filename = y.prepare_filename(info)
        mp3 = filename.rsplit(".", 1)[0] + ".mp3"

        return info, track_id, mp3


# ================================
# جستجو و انتخاب آهنگ
# ================================
async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    triggers = ["آهنگ ", "music ", "اغنية ", "أغنية "]

    if not any(text.lower().startswith(t) for t in triggers):
        return

    # محدودیت در گروه
    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    # تنظیمات زبان
    lang = "fa"
    for t in triggers:
        if text.lower().startswith(t):
            query = text[len(t):].strip()
            break

    msg = await update.message.reply_text(LANG_MESSAGES[lang]["searching"])

    # جستجو
    def _search():
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            return y.extract_info(f"scsearch5:{query}", download=False)

    loop = asyncio.get_running_loop()
    sc_info = await loop.run_in_executor(executor, _search)

    if not sc_info or not sc_info.get("entries"):
        await msg.edit_text(LANG_MESSAGES[lang]["notfound"])
        return

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
# دانلود انتخابی با کش
# ================================
async def music_select_handler(update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    chat = cq.message.chat_id

    # محدودیت در گروه
    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    track_id = cq.data.split(":")[1]

    # اگر در کش موجود است → ارسال فوری از تلگرام
    if track_id in SC_CACHE:
        file_id = SC_CACHE[track_id]["file_id"]
        await context.bot.send_audio(chat, file_id)
        return await cq.edit_message_text("⚡ ارسال سریع از کش تلگرام!")

    # ادامه → دانلود
    msg = await cq.edit_message_text("⬇️ در حال دانلود...")

    track_list = track_store.get(chat, [])
    track = next((t for t in track_list if str(t["id"]) == track_id), None)

    if not track:
        return await cq.edit_message_text("❌ آهنگ یافت نشد.")

    loop = asyncio.get_running_loop()

    info, tid, mp3 = await loop.run_in_executor(
        executor, _sc_download_sync, track["webpage_url"]
    )

    # ارسال فایل و ذخیره file_id
    sent = await context.bot.send_audio(chat, open(mp3, "rb"), caption="🎵 " + info["title"])

    SC_CACHE[tid] = {"file_id": sent.audio.file_id}
    save_cache()

    await msg.delete()
