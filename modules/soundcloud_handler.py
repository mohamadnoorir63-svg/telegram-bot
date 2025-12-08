# ================================
#     SoundCloud + YouTube Fallback
#       (FAST + NO FREEZE VERSION)
# ================================

import os
import shutil
import subprocess
import yt_dlp
import asyncio
from concurrent.futures import ThreadPoolExecutor
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# -------------------------------
# تنظیمات پایه
# -------------------------------
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

COOKIE_FILE = "modules/youtube_cookie.txt"   # ← از اینجا کوکی را می‌خواند
os.makedirs("modules", exist_ok=True)
if not os.path.exists(COOKIE_FILE):
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        f.write("# Paste YouTube cookies here in Netscape format\n")

executor = ThreadPoolExecutor(max_workers=5)
track_store = {}

# -------------------------------
# پیام‌های چندزبانه
# -------------------------------
LANG_MESSAGES = {
    "fa": {
        "searching": "🔍 در حال جستجو در SoundCloud ...",
        "downloading": "⬇️ در حال دانلود آهنگ...",
        "select_song": "🎵 {n} آهنگ پیدا شد. لطفا انتخاب کنید:",
        "yt_search": "🔎 هیچ آهنگی در SoundCloud پیدا نشد. در حال جستجو در یوتیوب ..."
    },
    "en": {
        "searching": "🔍 Searching SoundCloud ...",
        "downloading": "⬇️ Downloading song...",
        "select_song": "🎵 {n} songs found. Please select:",
        "yt_search": "🔎 No results on SoundCloud. Searching YouTube..."
    },
    "ar": {
        "searching": "🔍 جاري البحث في SoundCloud ...",
        "downloading": "⬇️ جاري تنزيل الأغنية...",
        "select_song": "🎵 تم العثور على {n} أغنية. الرجاء الاختيار:",
        "yt_search": "🔎 لا توجد نتائج في ساوند كلاود. جاري البحث في يوتيوب ..."
    },
}

# -------------------------------
# تبدیل به MP3 (Thread)
# -------------------------------
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

# -------------------------------
# دانلود SoundCloud (Thread)
# -------------------------------
def _download_track_sync(url):
    ydl_opts = {
        "quiet": True,
        "format": "bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    return info, filename

# -------------------------------
# دانلود از یوتیوب اگر SoundCloud خالی شد
# -------------------------------
def _download_youtube_sync(query):
    ydl_opts = {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "format": "bestaudio/best",
        "noplaylist": True,
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }
        ],
        "prefer_ffmpeg": True,
        "cachedir": False
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch1:{query}", download=True)

        if "entries" in info:
            info = info["entries"][0]

        filename = ydl.prepare_filename(info)

    base = filename.rsplit(".", 1)[0] + ".mp3"
    return info, base


# -------------------------------
#  هندلر اصلی SoundCloud
# -------------------------------
async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip().lower()
    triggers = ["آهنگ ", "music ", "اغنية ", "أغنية "]

    if not any(text.startswith(t) for t in triggers):
        return

    # -------------------------------
    # تشخیص زبان
    # -------------------------------
    lang = "fa"
    for t in triggers:
        if text.startswith(t):
            query = update.message.text[len(t):].strip()
            if t.startswith("music"):
                lang = "en"
            elif t.startswith(("اغنية", "أغنية")):
                lang = "ar"
            break

    context.user_data["music_lang"] = lang
    msg = await update.message.reply_text(LANG_MESSAGES[lang]["searching"])

    # -------------------------------
    # جستجو SoundCloud داخل Thread
    # -------------------------------
    def _sc_search():
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            return ydl.extract_info(f"scsearch10:{query}", download=False)

    loop = asyncio.get_running_loop()
    info = await loop.run_in_executor(executor, _sc_search)

    # اگر نتیجه نبود → یوتیوب
    if not info or "entries" not in info or not info["entries"]:
        await msg.edit_text(LANG_MESSAGES[lang]["yt_search"])

        try:
            yt_info, mp3_path = await loop.run_in_executor(
                executor, _download_youtube_sync, query
            )
        except Exception as e:
            return await msg.edit_text(f"❌ خطا:\n{e}")

        await context.bot.send_audio(
            update.effective_chat.id,
            mp3_path,
            caption=f"🎵 {yt_info.get('title', query)}"
        )

        os.remove(mp3_path)
        return

    # -------------------------------
    # نمایش لیست آهنگ‌ها
    # -------------------------------
    track_store[update.effective_chat.id] = info["entries"]

    keyboard = [
        [InlineKeyboardButton(t["title"], callback_data=f"music_select:{t['id']}")]
        for t in info["entries"]
    ]

    await msg.edit_text(
        LANG_MESSAGES[lang]["select_song"].format(n=len(info["entries"])),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# -------------------------------
# زمانی که کاربر از لیست SoundCloud یکی را انتخاب کند
# -------------------------------
async def music_select_handler(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    track_id = query.data.split(":")[1]
    chat_id = query.message.chat_id
    lang = context.user_data.get("music_lang", "fa")

    # پیدا کردن آهنگ
    track = next((t for t in track_store.get(chat_id, []) if str(t["id"]) == track_id), None)
    if not track:
        return await query.edit_message_text("❌ آهنگ پیدا نشد.")

    msg = await query.edit_message_text(LANG_MESSAGES[lang]["downloading"])

    loop = asyncio.get_running_loop()

    # دانلود داخل Thread
    info, filename = await loop.run_in_executor(executor, _download_track_sync, track["webpage_url"])

    # تبدیل MP3
    mp3_path = await loop.run_in_executor(executor, _convert_to_mp3_sync, filename)

    if mp3_path and os.path.exists(mp3_path):
        await context.bot.send_audio(chat_id, mp3_path, caption=f"🎵 {info.get('title')}")
        os.remove(mp3_path)

    if os.path.exists(filename):
        os.remove(filename)

    await msg.delete()
