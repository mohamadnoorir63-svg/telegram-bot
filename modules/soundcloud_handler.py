# ================================
# فایل: modules/soundcloud_handler.py
# ================================

import os
import asyncio
import yt_dlp
from concurrent.futures import ThreadPoolExecutor
import json
from typing import Optional

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# ================================
# سودو
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
# ThreadPool برای سرعت
# ================================
executor = ThreadPoolExecutor(max_workers=12)

# ================================
# جملات
# ================================
TXT = {
    "searching": "🔎 در حال جستجو...",
    "select": "🎵 {n} نتیجه یافت شد — انتخاب کنید:",
    "down": "⏳ دانلود موزیک از ربات دانلود آهنگ ...",
    "notfound": "⌛ ممکن است تا 15 ثانیه طول بکشد",
}

# ================================
# تنظیمات yt_dlp ultra-fast
# ================================
BASE_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "noprogress": True,
    "nopart": True,
    "noplaylist": True,
    "overwrites": True,
    "concurrent_fragment_downloads": 16,
    "ignoreerrors": True,
}

track_store = {}  # ذخیره نتایج SoundCloud

# ================================
# چک کش محلی
# ================================
def cache_check(id_: str) -> Optional[str]:
    for file in os.listdir(DOWNLOAD_FOLDER):
        if file.startswith(id_) and file.endswith(".mp3"):
            return os.path.join(DOWNLOAD_FOLDER, file)
    return None

# ================================
# دانلود SoundCloud ultra-fast
# ================================
def _sc_download_sync(url: str):
    opts = BASE_OPTS.copy()
    opts["postprocessors"] = []  # بدون تبدیل MP3 → مستقیم لینک صوتی
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)
        tid = str(info.get("id"))
        cached = cache_check(tid)
        if cached:
            return info, cached
        fname = y.prepare_filename(info)
        return info, fname

# ================================
# دانلود fallback یوتیوب مقاوم
# ================================
def _youtube_fallback_sync(query: str):
    opts = BASE_OPTS.copy()
    opts.update({
        "format": "bestaudio[abr<=128]/bestaudio",
        "concurrent_fragment_downloads": 20,
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "128"}
        ],
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s"
    })
    cookie_file = "modules/youtube_cookie.txt"
    if os.path.exists(cookie_file):
        opts["cookiefile"] = cookie_file

    with yt_dlp.YoutubeDL(opts) as y:
        try:
            info = y.extract_info(f"ytsearch1:{query}", download=True)
        except Exception:
            return None, None

        if not info:
            return None, None

        if "entries" in info and info["entries"]:
            info = info["entries"][0]

        if not info:
            return None, None

        vid = str(info.get("id", ""))
        if not vid:
            return None, None

        cached = cache_check(vid)
        if cached:
            return info, cached

        mp3_file = y.prepare_filename(info).rsplit(".", 1)[0] + ".mp3"
        if not os.path.exists(mp3_file):
            return None, None

        return info, mp3_file

# ================================
# هندلر پیام اصلی
# ================================
async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text
    triggers = ["آهنگ ", "music ", "اهنگ ", "موزیک "]
    if not any(text.lower().startswith(t) for t in triggers):
        return

    query = next((text[len(t):].strip() for t in triggers if text.lower().startswith(t)), "")

    msg = await update.message.reply_text(TXT["searching"])
    loop = asyncio.get_running_loop()

    # جستجوی SoundCloud
    def _search_sc():
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            return y.extract_info(f"scsearch10:{query}", download=False)

    try:
        result = await loop.run_in_executor(executor, _search_sc)
    except Exception:
        result = None

    # اگر SoundCloud نتیجه نداد → fallback یوتیوب
    if not result or not result.get("entries"):
        await msg.edit_text(TXT["notfound"])
        info, mp3 = await loop.run_in_executor(executor, _youtube_fallback_sync, query)

        if not info or not mp3:
            return await msg.edit_text("❌ یوتیوب چیزی پیدا نکرد!")

        cache_key = f"yt_{info.get('id')}"
        chat_id = update.message.chat.id

        buttons = None
        if update.effective_chat.type == "private":
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("افزودن به گروه", url=f"https://t.me/AFGR63_bot?startgroup=true")]
            ])

        # ارسال فایل از کش یا فایل جدید
        if cache_key in SC_CACHE:
            try: await msg.delete()
            except: pass
            return await update.message.reply_audio(
                SC_CACHE[cache_key],
                caption="🎵 ربات دانلود آهنگ",
                reply_markup=buttons
            )

        try:
            with open(mp3, "rb") as f:
                sent = await update.message.reply_audio(
                    f, caption="🎵 ربات دانلود آهنگ",
                    reply_markup=buttons
                )
        finally:
            if os.path.exists(mp3):
                os.remove(mp3)

        SC_CACHE[cache_key] = sent.audio.file_id
        save_cache()
        try: await msg.delete()
        except: pass
        return

    # SoundCloud نتیجه داد → دکمه انتخاب
    entries = {str(t["id"]): t for t in result["entries"]}
    track_store[update.message.message_id] = entries

    keyboard = [
        [InlineKeyboardButton(t["title"], callback_data=f"music_select:{update.message.message_id}:{tid}")]
        for tid, t in entries.items()
    ]

    await msg.edit_text(TXT["select"].format(n=len(entries)), reply_markup=InlineKeyboardMarkup(keyboard))

# ================================
# دکمه انتخاب آهنگ
# ================================
async def music_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()

    _, msg_id, tid = cq.data.split(":")
    msg_id = int(msg_id)
    tracks = track_store.get(msg_id, {})
    track = tracks.get(tid)

    if not track:
        return await cq.edit_message_text("❌ آهنگ یافت نشد.")

    cache_key = f"sc_{tid}"
    chat_id = cq.message.chat.id

    buttons = None
    if update.effective_chat.type == "private":
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("افزودن به گروه", url=f"https://t.me/AFGR63_bot?startgroup=true")]
        ])

    # ارسال از کش
    if cache_key in SC_CACHE:
        try:
            await cq.edit_message_text("⚡ در حال ارسال از کش تلگرام...")
        except Exception:
            pass
        return await context.bot.send_audio(chat_id, SC_CACHE[cache_key], reply_markup=buttons)

    # دانلود SoundCloud
    msg = await cq.edit_message_text(TXT["down"])
    loop = asyncio.get_running_loop()
    try:
        info, mp3 = await loop.run_in_executor(executor, _sc_download_sync, track["webpage_url"])
    except Exception as e:
        return await msg.edit_text(f"❌ خطا در دانلود:\n{e}")

    try:
        with open(mp3, "rb") as f:
            sent = await context.bot.send_audio(
                chat_id, f,
                caption="🎵 ربات دانلود آهنگ",
                reply_markup=buttons
            )
    finally:
        if os.path.exists(mp3):
            os.remove(mp3)

    SC_CACHE[cache_key] = sent.audio.file_id
    save_cache()
    try: await msg.delete()
    except: pass
