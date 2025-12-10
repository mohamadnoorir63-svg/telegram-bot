import os
import asyncio
import yt_dlp
from concurrent.futures import ThreadPoolExecutor
import io
import json
from typing import Optional, Tuple

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# ================================================
# سودو
# ================================================
SUDO_USERS = [8588347189]

# ================================================
# تنظیمات مسیرها و کش
# ================================================
DATA_FOLDER = "data"
DOWNLOAD_FOLDER = "downloads"
CACHE_FILE = os.path.join(DATA_FOLDER, "sc_cache.json")

os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

if not os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

with open(CACHE_FILE, "r", encoding="utf-8") as f:
    try:
        SC_CACHE = json.load(f)
    except Exception:
        SC_CACHE = {}


def save_cache():
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(SC_CACHE, f, indent=2, ensure_ascii=False)


# ================================================
# ThreadPool برای async
# ================================================
executor = ThreadPoolExecutor(max_workers=12)

# ================================================
# جملات
# ================================================
TXT = {
    "searching": "🔍",
    "select": "🎶",
    "down": "⏳",
    "notfound": "⌛ نتیجه بهتر",
    "error": "❌⚠️"
}

# ================================================
# CAPTION ثابت موزیک
# ================================================
MUSIC_CAPTION = "[دانلود موزیک با ربات](@AFGR63_bot)"
# ================================================
# دکمه افزودن به گروه (فقط در پیوی)
# ================================================
ADD_BTN = InlineKeyboardMarkup([
    [InlineKeyboardButton("➕ افزودن ربات به گروه", url="https://t.me/AFGR63_bot?startgroup=true")]
])

# ================================================
# تنظیمات yt_dlp
# ================================================
BASE_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "noprogress": True,
    "nopart": True,
    "noplaylist": True,
    "overwrites": True,
    "concurrent_fragment_downloads": 16,
}

track_store = {}

# ================================================
# کمکی: بررسی کش محلی
# prefix: 'sc' یا 'yt'
# returns: cached file_id or None
# ================================================
def cache_check(vid: str, prefix: str = "sc") -> Optional[str]:
    key = f"{prefix}_{vid}"
    return SC_CACHE.get(key)


# ================================================
# دانلود SoundCloud (bytes)
# ================================================
def _sc_download_sync_bytes(url: str) -> Tuple[dict, bytes]:
    opts = BASE_OPTS.copy()
    opts["postprocessors"] = []
    opts["outtmpl"] = os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s")

    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)

        fname = y.prepare_filename(info)

        with open(fname, "rb") as f:
            audio_bytes = f.read()

        try:
            os.remove(fname)
        except OSError:
            pass

        return info, audio_bytes


async def _sc_download_bytes(url: str) -> Tuple[dict, bytes]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, _sc_download_sync_bytes, url)


# ================================================
# fallback YouTube → MP3 واقعی
# ================================================
def _youtube_fallback_sync(query: str) -> Tuple[dict, str]:
    opts = BASE_OPTS.copy()
    opts["concurrent_fragment_downloads"] = 20

    cookie_file = os.path.join("modules", "youtube_cookie.txt")
    if os.path.exists(cookie_file):
        opts["cookiefile"] = cookie_file

    opts["format"] = "bestaudio/best"
    opts["noplaylist"] = True
    opts["postprocessors"] = [
        {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
    ]
    opts["outtmpl"] = os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s")

    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(f"ytsearch1:{query}", download=True)

        if "entries" in info and info["entries"]:
            info = info["entries"][0]

        vid = str(info["id"])

        cached = cache_check(vid, prefix="yt")
        if cached:
            return info, cached

        mp3 = y.prepare_filename(info).rsplit(".", 1)[0] + ".mp3"
        if not os.path.exists(mp3):
            raise FileNotFoundError(f"mp3 پیدا نشد.")

        return info, mp3


async def _youtube_fallback(query: str):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, _youtube_fallback_sync, query)


# ================================================
# جستجو و fallback
# ================================================
async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text
    triggers = ["آهنگ ", "music ", "اهنگ " , "Musik", "Music", "موزیک", "اغنية" ,"أغنية"]
    if not any(text.lower().startswith(t) for t in triggers):
        return

    query = next(
        (text[len(t):].strip() for t in triggers if text.lower().startswith(t)),
        ""
    )

    msg = await update.message.reply_text(TXT["searching"])

    loop = asyncio.get_running_loop()

    def _search_sc():
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            return y.extract_info(f"scsearch10:{query}", download=False)

    try:
        result = await loop.run_in_executor(executor, _search_sc)
    except Exception:
        result = None

    # ================================
    # Fallback YouTube اگر SC نتیجه نداد
    # ================================
    if not result or not result.get("entries"):
        await msg.edit_text("🔁 SoundCloud نتیجه نداشت — جستجو در YouTube...")

        try:
            info, path_or_fileid = await _youtube_fallback(query)
        except Exception as e:
            await msg.edit_text(f"{TXT['notfound']} ({e})")
            return

        chat_id = update.message.chat.id

        # اگر file_id است → ارسال مستقیم
        if isinstance(path_or_fileid, str) and path_or_fileid.startswith("BQ"):
            await context.bot.send_audio(
                chat_id,
                path_or_fileid,
                caption=MUSIC_CAPTION,
                reply_markup=ADD_BTN if update.message.chat.type == "private" else None
            )
            await msg.delete()
            return

        # فایل mp3 جدید
        mp3_path = path_or_fileid
        with open(mp3_path, "rb") as f:
            audio_io = io.BytesIO(f.read())
        audio_io.name = f"{info.get('title','music')}.mp3"

        sent = await context.bot.send_audio(
            chat_id,
            audio_io,
            caption=MUSIC_CAPTION,
            reply_markup=ADD_BTN if update.message.chat.type == "private" else None
        )

        SC_CACHE[f"yt_{info['id']}"] = sent.audio.file_id
        save_cache()

        try:
            os.remove(mp3_path)
        except:
            pass

        await msg.delete()
        return

    # ================================
    # نتایج SoundCloud
    # ================================
    entries = {str(t["id"]): t for t in result["entries"]}
    track_store[update.message.message_id] = entries

    keyboard = [
        [InlineKeyboardButton(t["title"], callback_data=f"music_select:{update.message.message_id}:{tid}")]
        for tid, t in entries.items()
    ]

    await msg.edit_text(
        TXT["select"].format(n=len(entries)),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================================================
# انتخاب آهنگ از SoundCloud
# ================================================
async def music_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()

    _, msg_id, tid = cq.data.split(":")
    msg_id = int(msg_id)

    track = track_store.get(msg_id, {}).get(tid)
    if not track:
        return await cq.edit_message_text("❌ آهنگ یافت نشد.")

    cache_key = f"sc_{tid}"
    chat_id = cq.message.chat.id

    # اگر کش موجود بود
    if cache_key in SC_CACHE:
        return await context.bot.send_audio(
            chat_id,
            SC_CACHE[cache_key],
            caption=MUSIC_CAPTION,
            reply_markup=ADD_BTN if cq.message.chat.type == "private" else None
        )

    msg = await cq.edit_message_text(TXT["down"])

    try:
        info, audio_bytes = await _sc_download_bytes(track["webpage_url"])
    except Exception as e:
        await msg.edit_text(f"{TXT['error']} {e}")
        return

    audio_io = io.BytesIO(audio_bytes)
    audio_io.name = f"{info.get('title','music')}.mp3"

    sent = await context.bot.send_audio(
        chat_id,
        audio_io,
        caption=MUSIC_CAPTION,
        reply_markup=ADD_BTN if cq.message.chat.type == "private" else None
    )

    SC_CACHE[cache_key] = sent.audio.file_id
    save_cache()

    await msg.delete()
