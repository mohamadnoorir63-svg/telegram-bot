# modules/soundcloud_handler.py

import os
import json
import asyncio
import yt_dlp
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
CACHE_FILE = "data/sound_cache.json"
COOKIE_FILE = "modules/youtube_cookie.txt"

os.makedirs("downloads", exist_ok=True)
os.makedirs("data", exist_ok=True)

# ساخت کش اگر نبود
if not os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "w") as f:
        json.dump({}, f)

# بارگذاری کش
with open(CACHE_FILE, "r") as f:
    SC_CACHE = json.load(f)

# ذخیره کش
def save_cache():
    with open(CACHE_FILE, "w") as f:
        json.dump(SC_CACHE, f, indent=4)

executor = ThreadPoolExecutor(max_workers=8)

# کش انتخاب و لیست جستجو
track_store = {}

# ================================
# پیام‌ها
# ================================
LANG_MESSAGES = {
    "fa": {
        "searching": "🔍 در حال جستجو ...",
        "downloading": "⬇️ دانلود...",
        "select_song": "🎵 {n} آهنگ پیدا شد — انتخاب کنید:",
        "notfound": "❌ در SoundCloud چیزی نبود، دارم از یوتیوب می‌گردم...",
    },
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

    admins = await context.bot.get_chat_administrators(chat.id)
    admin_ids = [a.user.id for a in admins]
    return user.id in admin_ids


# ================================
# دانلود SoundCloud (با کش)
# ================================
def _sc_download_sync(url):
    opts = {
        "quiet": True,
        "format": "bestaudio/best",
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)

    file = y.prepare_filename(info)
    mp3 = file.rsplit(".", 1)[0] + ".mp3"

    return info, mp3


# ================================
# دانلود fallback یوتیوب (با کش)
# ================================
def _youtube_fallback_sync(query):
    opts = {
        "quiet": True,
        "cookiefile": COOKIE_FILE,
        "format": "bestaudio/best",
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(f"ytsearch1:{query}", download=True)

        if "entries" in info:
            info = info["entries"][0]

    file = y.prepare_filename(info)
    mp3 = file.rsplit(".", 1)[0] + ".mp3"

    return info, mp3


# ================================
# جستجو و انتخاب SoundCloud
# ================================
async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    if not (text.startswith("آهنگ") or text.lower().startswith("music")):
        return

    # گروه → فقط مدیران
    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    query = text.split(" ", 1)[1].strip()
    msg = await update.message.reply_text(LANG_MESSAGES["fa"]["searching"])

    # جستجو در SoundCloud
    def _search():
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            return y.extract_info(f"scsearch5:{query}", download=False)

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(executor, _search)

    if not result or not result.get("entries"):
        await msg.edit_text(LANG_MESSAGES["fa"]["notfound"])

        info, mp3 = await loop.run_in_executor(executor, _youtube_fallback_sync, query)

        # چک کش یوتیوب
        vid = info["id"]
        if vid in SC_CACHE:
            try:
                return await update.message.reply_audio(SC_CACHE[vid])
            except:
                del SC_CACHE[vid]
                save_cache()

        sent = await update.message.reply_audio(open(mp3, "rb"), caption=info["title"])

        SC_CACHE[vid] = sent.audio.file_id
        save_cache()
        os.remove(mp3)
        return

    entries = result["entries"]
    track_store[update.effective_chat.id] = entries

    keyboard = [
        [InlineKeyboardButton(t["title"], callback_data=f"scsel:{t['id']}")]
        for t in entries
    ]

    await msg.edit_text(
        LANG_MESSAGES["fa"]["select_song"].format(n=len(entries)),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ================================
# دانلود ترک انتخاب‌شده
# ================================
async def music_select_handler(update, context: ContextTypes.DEFAULT_TYPE):

    cq = update.callback_query
    await cq.answer()
    chat = cq.message.chat_id

    # گروه → فقط مدیر
    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    tid = cq.data.split(":")[1]

    tracks = track_store.get(chat, [])
    track = next((t for t in tracks if str(t["id"]) == tid), None)

    if not track:
        return await cq.edit_message_text("❌ پیدا نشد.")

    # اگر در کش داریم
    if tid in SC_CACHE:
        try:
            return await context.bot.send_audio(chat, SC_CACHE[tid])
        except:
            # اگر file_id خراب شد → پاک شود
            del SC_CACHE[tid]
            save_cache()

    await cq.edit_message_text("⬇ دانلود...")

    loop = asyncio.get_running_loop()
    info, mp3 = await loop.run_in_executor(executor, _sc_download_sync, track["webpage_url"])

    sent = await context.bot.send_audio(chat, open(mp3, "rb"), caption=info["title"])

    # ذخیره file_id
    SC_CACHE[tid] = sent.audio.file_id
    save_cache()

    os.remove(mp3)
