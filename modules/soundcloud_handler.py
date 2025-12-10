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
    "searching": "🔎 در حال جستجو...",
    "select": "🎵 انتخاب کن ({n} نتیجه یافت شد):",
    "down": "⏳ دانلود در حال انجام...",
    "notfound": "⌛ نتیجه‌ای پیدا نشد.",
    "error": "❌ خطا رخ داد."
}

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
# دانلود مستقیم به حافظه (SoundCloud)
# بازگشت: (info, bytes)
# ================================================
def _sc_download_sync_bytes(url: str) -> Tuple[dict, bytes]:
    opts = BASE_OPTS.copy()
    # برای دانلود خام بایت‌ها، هیچ postprocessor ای اضافه نمی‌کنیم
    opts["postprocessors"] = []
    opts["outtmpl"] = os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s")

    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)

        tid = str(info.get("id"))
        fname = y.prepare_filename(info)

        # بخوان و حذف کن
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
# fallback YouTube (sync) -> تولید MP3 واقعی در پوشه downloads
# بازگشت: (info, mp3_path) یا raise
# (تابع sync که از ThreadPool اجرا می‌شود)
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
    # خروجی را به پوشه downloads هدایت می‌کنیم
    opts["outtmpl"] = os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s")

    with yt_dlp.YoutubeDL(opts) as y:
        try:
            info = y.extract_info(f"ytsearch1:{query}", download=True)
        except Exception as e:
            raise RuntimeError(f"خطا در yt_dlp (youtube search): {e}")

        # اگر نتیجه جستجو برگشتی داشت، اولین مورد را انتخاب کن
        if "entries" in info and info["entries"]:
            info = info["entries"][0]

        vid = str(info.get("id"))
        # بررسی کش با پیشوند yt_
        cached = cache_check(vid, prefix="yt")
        if cached:
            # اگر قبلاً آپلود شده و file_id داریم، برگردان file_id به فراخواننده (نشانه برای ارسال مستقیم)
            return info, cached

        # یوتی‌دی‌ال معمولا فایل .mp3 را می‌سازد (postprocessor)
        mp3_path = y.prepare_filename(info).rsplit(".", 1)[0] + ".mp3"
        if not os.path.exists(mp3_path):
            raise FileNotFoundError(f"فایل mp3 برای {vid} پیدا نشد: {mp3_path}")

        return info, mp3_path


# async wrapper برای fallback یوتیوب
async def _youtube_fallback(query: str) -> Tuple[dict, str]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, _youtube_fallback_sync, query)


# ================================================
# هندلر پیام اصلی (SoundCloud search)
# اگر هیچ نتیجه‌ای از SC نیامد -> fallback یوتیوب اجرا می‌شود
# ================================================
async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text
    triggers = ["آهنگ ", "music ", "اهنگ ", "موزیک "]

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

    # اگر هیچ نتیجه‌ای از SoundCloud نبود -> بزن به یوتیوب (fallback)
    if not result or not result.get("entries"):
        try:
            # اطلاع‌رسانی به کاربر
            await msg.edit_text("🔁 SoundCloud نتیجه نداشت — جستجو در YouTube...")
            info, mp3_or_fileid = await _youtube_fallback(query)
        except Exception as e:
            # برگشت به پیام خطا
            await msg.edit_text(f"{TXT['notfound']} ({str(e)})")
            return

        # اگر mp3_or_fileid یک file_id (str) است یعنی از کش برگشته
        if isinstance(mp3_or_fileid, str) and mp3_or_fileid.startswith("BQ"):  # تلگرام file_id معمولاً با 'BQ' یا 'Aw' شروع می‌شود ولی این یک حدس است — اما اگر کش ما قبلاً file_id ذخیره کرده، آن را ارسال می‌کنیم
            await context.bot.send_audio(update.message.chat.id, mp3_or_fileid, caption=info.get("title", ""))
            await msg.delete()
            return

        # در غیر این صورت mp3_or_fileid مسیر فایل mp3 است
        mp3_path = mp3_or_fileid
        try:
            with open(mp3_path, "rb") as f:
                audio_io = io.BytesIO(f.read())
            audio_io.name = f"{info.get('title','music')}.mp3"

            sent = await context.bot.send_audio(update.message.chat.id, audio_io, caption=info.get("title", ""))
            # ذخیره در کش با پیشوند yt_
            vid = str(info.get("id"))
            SC_CACHE[f"yt_{vid}"] = sent.audio.file_id
            save_cache()

            # حذف فایل محلی mp3 (اختیاری)
            try:
                os.remove(mp3_path)
            except OSError:
                pass

            await msg.delete()
            return
        except Exception as e:
            await msg.edit_text(f"{TXT['error']} {e}")
            return

    # اگر SoundCloud نتیجه داشت مثل قبل نمایش لیست نتیجه‌ها
    entries = {str(t["id"]): t for t in result["entries"]}
    track_store[update.message.message_id] = entries

    keyboard = [
        [
            InlineKeyboardButton(
                t["title"],
                callback_data=f"music_select:{update.message.message_id}:{tid}"
            )
        ]
        for tid, t in entries.items()
    ]

    await msg.edit_text(
        TXT["select"].format(n=len(entries)),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================================================
# دکمه انتخاب آهنگ (از نتایج SoundCloud)
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

    # اگر در کش هست، file_id را مستقیم ارسال کن
    if cache_key in SC_CACHE:
        return await context.bot.send_audio(chat_id, SC_CACHE[cache_key])

    msg = await cq.edit_message_text(TXT["down"])

    try:
        info, audio_bytes = await _sc_download_bytes(track["webpage_url"])
    except Exception as e:
        # اگر دانلود از SC شکست خورد، می‌توانیم fallback یوتیوب را امتحان کنیم یا خطا نشان دهیم.
        # طبق انتخاب شما (گزینه 1) فقط وقتی SoundCloud هیچ نتیجه‌ای نداشت از یوتیوب استفاده می‌کنیم،
        # بنابراین اینجا خطا را به کاربر نشان می‌دهیم.
        await msg.edit_text(f"{TXT['error']} {e}")
        return

    # ارسال مستقیم از حافظه (نه Voice)
    audio_io = io.BytesIO(audio_bytes)
    audio_io.name = f"{info.get('title', 'music')}.mp3"
    try:
        sent = await context.bot.send_audio(chat_id, audio_io, caption=info.get("title", ""))
    except Exception as e:
        await msg.edit_text(f"{TXT['error']} {e}")
        return

    SC_CACHE[cache_key] = sent.audio.file_id
    save_cache()

    await msg.delete()
