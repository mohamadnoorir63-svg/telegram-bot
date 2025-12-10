# modules/soundcloud_handler.py
import os
import shutil
import subprocess
import yt_dlp
import asyncio
import re
from concurrent.futures import ThreadPoolExecutor
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# ================================
# تنظیمات
# ================================

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

COOKIE_FILE = "modules/youtube_cookie.txt"   # ← کوکی یوتیوب از این فایل

executor = ThreadPoolExecutor(max_workers=5)
track_store = {}

LANG_MESSAGES = {
    "fa": {
        "searching": "🔍 در حال جستجو در SoundCloud ...",
        "downloading": "⬇️ در حال دانلود آهنگ... لطفا صبر کنید.",
        "select_song": "🎵 {n} آهنگ پیدا شد. لطفا انتخاب کنید:",
        "notfound": "❌ آهنگی در SoundCloud پیدا نشد. در حال جستجو در یوتیوب..."
    },
    "en": {
        "searching": "🔍 Searching SoundCloud...",
        "downloading": "⬇️ Downloading... please wait.",
        "select_song": "🎵 {n} songs found. Please choose:",
        "notfound": "❌ No SoundCloud results found. Searching YouTube..."
    },
    "ar": {
        "searching": "🔍 جاري البحث في SoundCloud ...",
        "downloading": "⬇️ جاري التحميل...",
        "select_song": "🎵 {n} أغنية. الرجاء الاختيار:",
        "notfound": "❌ لم يتم العثور على نتائج. جاري البحث في YouTube..."
    },
}


# ================================
# تبدیل به MP3 (Thread)
# ================================
def _convert_to_mp3_sync(filepath):
    mp3_path = filepath.rsplit(".", 1)[0] + ".mp3"
    if not shutil.which("ffmpeg"):
        return None

    subprocess.run([
        "ffmpeg", "-y", "-i", filepath,
        "-vn", "-ab", "192k", "-ar", "44100",
        mp3_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return mp3_path


# ================================
# دانلود از SoundCloud (Thread)
# ================================
def _download_track_sync(url):
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
    return info, filename


# ================================
# Fallback به یوتیوب — جستجو و دانلود MP3
# ================================
def _youtube_fallback_sync(query):
    ydl_opts = {
        "cookiefile": COOKIE_FILE,     # ← استفاده از کوکی
        "quiet": True,
        "format": "bestaudio/best",
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192"
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch1:{query}", download=True)
        if "entries" in info:
            info = info["entries"][0]

        filename = ydl.prepare_filename(info)
        mp3_file = filename.rsplit(".", 1)[0] + ".mp3"

    return info, mp3_file


# ================================
# هندلر اصلی جستجو
# ================================
async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    triggers = ["آهنگ ", "music ", "اغنية ", "أغنية "]
    if not any(text.lower().startswith(t) for t in triggers):
        return

    lang = "fa"
    for t in triggers:
        if text.lower().startswith(t):
            query = text[len(t):].strip()
            lang = "en" if t.startswith("music") else ("ar" if t.startswith(("اغنية","أغنية")) else "fa")
            break

    msg = await update.message.reply_text(LANG_MESSAGES[lang]["searching"])

    # اجرای جستجو در Thread
    def search_soundcloud():
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            return ydl.extract_info(f"scsearch10:{query}", download=False)

    loop = asyncio.get_running_loop()
    try:
        info = await loop.run_in_executor(executor, search_soundcloud)
    except:
        info = None

    # اگر SoundCloud چیزی پیدا نکرد → برو یوتیوب
    if not info or "entries" not in info or len(info["entries"]) == 0:
        await msg.edit_text(LANG_MESSAGES[lang]["notfound"])

        try:
            yt_info, mp3_path = await loop.run_in_executor(
                executor, _youtube_fallback_sync, query
            )
        except Exception as e:
            return await msg.edit_text(f"❌ خطا:\n{e}")

        with open(mp3_path, "rb") as f:
            await update.message.reply_audio(audio=f, caption=f"🎵 {yt_info.get('title','Music')}")

        os.remove(mp3_path)
        return

    # اگر نتیجه SoundCloud پیدا شد → لیست بده
    track_store[update.effective_chat.id] = info["entries"]

    keyboard = [
        [InlineKeyboardButton(t["title"], callback_data=f"music_select:{t['id']}")]
        for t in info["entries"]
    ]

    await msg.edit_text(
        LANG_MESSAGES[lang]["select_song"].format(n=len(info["entries"])),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================================
# هندلر انتخاب آهنگ
# ================================
async def music_select_handler(update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    track_id = query.data.split(":")[1]
    chat_id = query.message.chat_id

    tracks = track_store.get(chat_id, [])
    track = next((t for t in tracks if str(t["id"]) == track_id), None)

    if not track:
        return await query.edit_message_text("❌ آهنگ پیدا نشد.")

    msg = await query.edit_message_text("⬇️ در حال دانلود...")

    loop = asyncio.get_running_loop()
    info, file_path = await loop.run_in_executor(executor, _download_track_sync, track["webpage_url"])
    mp3_path = await loop.run_in_executor(executor, _convert_to_mp3_sync, file_path)

    if mp3_path:
        with open(mp3_path, "rb") as f:
            await context.bot.send_audio(chat_id, f, caption=f"🎵 {info.get('title')}")
        os.remove(mp3_path)

    os.remove(file_path)
    await msg.delete()
