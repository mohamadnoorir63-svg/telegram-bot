# ================================
# modules/soundcloud_handler.py
# نسخه با کش تلگرام (file_id) بدون تغییر ساختار اصلی
# ================================

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
SUDO_USERS = [8588347189]

# ================================
# تنظیمات
# ================================
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

COOKIE_FILE = "modules/youtube_cookie.txt"

executor = ThreadPoolExecutor(max_workers=8)

track_store = {}

# ================================
# فایل کش تلگرام
# ================================
CACHE_FILE = "data/soundcloud_cache.json"
os.makedirs("data", exist_ok=True)

if not os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "w") as fp:
        json.dump({}, fp)

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
    },
    "en": {
        "searching": "🔍 Searching... please wait",
        "downloading": "⬇️ Downloading...",
        "select_song": "🎵 {n} songs found — choose one:",
        "notfound": "❌ No results in SoundCloud. Searching YouTube...",
    },
    "ar": {
        "searching": "🔍 جاري البحث ... يرجى الانتظار",
        "downloading": "⬇️ جاري تنزيل الأغنية...",
        "select_song": "🎵 تم العثور على {n} أغنية — يرجى الاختيار:",
        "notfound": "❌ لا توجد نتائج في ساوند كلاود. يتم البحث في يوتيوب...",
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
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "192",
    }],
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
# چک فایل mp3 روی دیسک
# ================================
def cache_check_file(id_: str):
    """اگر mp3 لوکال قبلاً دانلود شده باشد"""
    for f in os.listdir(DOWNLOAD_FOLDER):
        if f.startswith(id_) and f.endswith(".mp3"):
            return os.path.join(DOWNLOAD_FOLDER, f)
    return None

# ================================
# دانلود SoundCloud (Turbo + Cache)
# ================================
def _sc_download_sync(url: str):
    opts = BASE_OPTS.copy()

    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)

        track_id = str(info.get("id"))

        # اگر فایل mp3 قبلاً وجود دارد
        cached_file = cache_check_file(track_id)
        if cached_file:
            return info, cached_file

        fname = y.prepare_filename(info)
        mp3 = fname.rsplit(".", 1)[0] + ".mp3"
        return info, mp3


# ================================
# fallback یوتیوب (Turbo + Cache)
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

        cached_file = cache_check_file(vid)
        if cached_file:
            return info, cached_file

        fname = y.prepare_filename(info)
        mp3 = fname.rsplit(".", 1)[0] + ".mp3"
        return info, mp3


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

    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    lang = "fa"
    query = ""
    for t in triggers:
        if text.lower().startswith(t):
            query = text[len(t):].strip()
            lang = "en" if t.startswith("music") else ("ar" if "غ" in t else "fa")
            break

    msg = await update.message.reply_text(LANG_MESSAGES[lang]["searching"])

    def _search():
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            return y.extract_info(f"scsearch3:{query}", download=False)

    loop = asyncio.get_running_loop()
    sc_info = await loop.run_in_executor(executor, _search)

    if not sc_info or not sc_info.get("entries"):

        await msg.edit_text(LANG_MESSAGES[lang]["notfound"])

        info, mp3 = await loop.run_in_executor(executor, _youtube_fallback_sync, query)

        sent = await update.message.reply_audio(open(mp3, "rb"), caption=f"🎵 {info['title']}")

        # ذخیره file_id
        SC_CACHE[str(info["id"])] = sent.audio.file_id
        save_cache()

        return

    entries = sc_info["entries"]
    track_store[update.effective_chat.id] = entries

    keyboard = [
        [InlineKeyboardButton(t["title"], callback_data=f"music_select:{t['id']}")]
        for t in entries
    ]

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

    # اگر در کش تلگرام موجود است → ارسال مستقیم
    if track_id in SC_CACHE:
        return await context.bot.send_audio(chat, SC_CACHE[track_id])

    tracks = track_store.get(chat, [])
    track = next((t for t in tracks if str(t["id"]) == track_id), None)

    if not track:
        return await cq.edit_message_text("❌ آهنگ پیدا نشد.")

    await cq.edit_message_text("⬇️ در حال دانلود...")

    loop = asyncio.get_running_loop()
    info, mp3 = await loop.run_in_executor(
        executor, _sc_download_sync, track["webpage_url"]
    )

    sent = await context.bot.send_audio(chat, open(mp3, "rb"), caption=f"🎵 {info['title']}")

    # ذخیره file_id در کش
    SC_CACHE[track_id] = sent.audio.file_id
    save_cache()
