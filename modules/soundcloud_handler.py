# modules/soundcloud_handler.py
import os
import shutil
import subprocess
import yt_dlp
import asyncio
from concurrent.futures import ThreadPoolExecutor
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

executor = ThreadPoolExecutor(max_workers=5)
track_store = {}

LANG_MESSAGES = {
    "fa": {
        "searching": "🔍 در حال جستجو در SoundCloud ...",
        "downloading": "⬇️ در حال دانلود آهنگ... لطفا صبر کنید.",
        "select_song": "🎵 {n} آهنگ پیدا شد. لطفا انتخاب کنید:"
    },
    "en": {
        "searching": "🔍 Searching in SoundCloud ...",
        "downloading": "⬇️ Downloading song... Please wait.",
        "select_song": "🎵 {n} songs found. Please select:"
    },
    "ar": {
        "searching": "🔍 جاري البحث في SoundCloud ...",
        "downloading": "⬇️ جاري تنزيل الأغنية... يرجى الانتظار.",
        "select_song": "🎵 تم العثور على {n} أغنية. الرجاء الاختيار:"
    },
}

def _download_track_sync(url):
    """ اجرای yt-dlp داخل Thread — بدون هنگ """
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
    return info, filename


def _convert_to_mp3_sync(filepath):
    """ ffmpeg داخل Thread — بدون هنگ """
    mp3_path = filepath.rsplit(".", 1)[0] + ".mp3"
    if not shutil.which("ffmpeg"):
        return None
    subprocess.run([
        "ffmpeg", "-y", "-i", filepath,
        "-vn", "-ab", "192k", "-ar", "44100",
        mp3_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return mp3_path


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

    # جستجو در Thread (ممنوع داخل async)
    def search_soundcloud():
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            return ydl.extract_info(f"scsearch10:{query}", download=False)

    try:
        loop = asyncio.get_running_loop()
        info = await loop.run_in_executor(executor, search_soundcloud)
    except:
        return await msg.edit_text("❌ خطا در جستجو.")

    if not info or "entries" not in info:
        return await msg.edit_text("❌ هیچ آهنگی پیدا نشد.")

    track_store[update.effective_chat.id] = info["entries"]

    keyboard = [
        [InlineKeyboardButton(t["title"], callback_data=f"music_select:{t['id']}")]
        for t in info["entries"]
    ]

    await msg.edit_text(
        LANG_MESSAGES[lang]["select_song"].format(n=len(info["entries"])),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def music_select_handler(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    track_id = query.data.split(":")[1]
    chat_id = query.message.chat_id
    lang = context.user_data.get("music_lang", "fa")

    track = next((t for t in track_store.get(chat_id, []) if str(t["id"]) == track_id), None)
    if not track:
        return await query.edit_message_text("❌ آهنگ پیدا نشد.")

    msg = await query.edit_message_text(LANG_MESSAGES[lang]["downloading"])

    loop = asyncio.get_running_loop()

    # دانلود آهنگ داخل Thread
    info, filename = await loop.run_in_executor(executor, _download_track_sync, track["webpage_url"])

    # تبدیل به MP3 داخل Thread
    mp3_path = await loop.run_in_executor(executor, _convert_to_mp3_sync, filename)

    if mp3_path and os.path.exists(mp3_path):
        await context.bot.send_audio(chat_id, mp3_path, caption=f"🎵 {info.get('title')}")
        os.remove(mp3_path)

    os.remove(filename)
    await msg.delete()
