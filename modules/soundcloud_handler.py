# modules/soundcloud_handler.py
import os
import subprocess
import yt_dlp
import asyncio
from concurrent.futures import ThreadPoolExecutor
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes


# ========================
#  تنظیمات سرعت بالا
# ========================
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

COOKIE_FILE = "modules/youtube_cookie.txt"
executor = ThreadPoolExecutor(max_workers=12)   # ← افزایش سرعت


# ========================
#  پیام‌ها
# ========================
MSG = {
    "fa": {
        "searching": "🔍 در حال جستجو…",
        "select": "🎵 {n} آهنگ پیدا شد — انتخاب کنید:",
        "downloading": "⬇️ در حال دانلود آهنگ…",
        "yt_fallback": "❌ در SoundCloud چیزی نبود — جستجو در یوتیوب...",
    }
}


# ========================
#  دانلود SoundCloud (Turbo)
# ========================
def sc_download_sync(url):
    opts = {
        "quiet": True,
        "format": "bestaudio/best",
        "concurrent_fragment_downloads": 10,     # سرعت بالا
        "fragment_retries": 20,
        "retries": 15,
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    }
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)
        file = y.prepare_filename(info)
    return info, file


# ========================
#  تبدیل Turbo MP3
# ========================
def fast_mp3_sync(path):
    mp3 = path.rsplit(".", 1)[0] + ".mp3"
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", path,
            "-vn", "-b:a", "192k",
            "-threads", "4",           # ← سریع‌تر
            mp3
        ],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    return mp3


# ========================
#  fallback سریع یوتیوب
# ========================
def yt_fallback_sync(q):
    opts = {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "format": "bestaudio/best",
        "concurrent_fragment_downloads": 10,
        "fragment_retries": 20,
        "retries": 15,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192"
        }],
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    }
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(f"ytsearch1:{q}", download=True)
        if "entries" in info:
            info = info["entries"][0]
        file = y.prepare_filename(info).rsplit(".", 1)[0] + ".mp3"
    return info, file


# ذخیره نتایج
track_store = {}

# ========================
#  Handler جستجو
# ========================
async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    txt = update.message.text.strip()
    if not txt.startswith("آهنگ "):
        return

    query = txt.replace("آهنگ ", "").strip()
    msg = await update.message.reply_text(MSG["fa"]["searching"])

    # ---------- جستجوی SoundCloud ----------
    def search_sc():
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            return y.extract_info(f"scsearch10:{query}", download=False)

    loop = asyncio.get_running_loop()
    try:
        info = await loop.run_in_executor(executor, search_sc)
    except:
        info = None

    # ---------- اگر نتیجه نبود → یوتیوب ----------
    if not info or "entries" not in info or not info["entries"]:
        await msg.edit_text(MSG["fa"]["yt_fallback"])

        try:
            yt_info, mp3 = await loop.run_in_executor(executor, yt_fallback_sync, query)
        except Exception as e:
            return await msg.edit_text(f"❌ خطا:\n{e}")

        with open(mp3, "rb") as f:
            await update.message.reply_audio(f, caption=f"🎵 {yt_info['title']}")

        os.remove(mp3)
        return

    # ---------- ساخت لیست ----------
    entries = info["entries"]
    track_store[update.effective_chat.id] = entries

    keyboard = [
        [InlineKeyboardButton(t["title"], callback_data=f"msc:{t['id']}")]
        for t in entries
    ]

    await msg.edit_text(
        MSG["fa"]["select"].format(n=len(entries)),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ========================
#  انتخاب آهنگ
# ========================
async def music_select_handler(update, context):

    cq = update.callback_query
    await cq.answer()

    chat = cq.message.chat_id
    track_id = cq.data.split(":")[1]

    tracks = track_store.get(chat, [])
    track = next((t for t in tracks if str(t["id"]) == track_id), None)

    if not track:
        return await cq.edit_message_text("❌ آهنگ پیدا نشد.")

    msg = await cq.edit_message_text(MSG["fa"]["downloading"])

    loop = asyncio.get_running_loop()

    # دانلود
    info, audio = await loop.run_in_executor(executor, sc_download_sync, track["webpage_url"])

    # تبدیل
    mp3 = await loop.run_in_executor(executor, fast_mp3_sync, audio)

    with open(mp3, "rb") as f:
        await context.bot.send_audio(chat, f, caption=f"🎵 {info['title']}")

    os.remove(mp3)
    os.remove(audio)
    await msg.delete()
