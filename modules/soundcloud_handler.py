# modules/soundcloud_handler.py
import os
import yt_dlp
import asyncio
from concurrent.futures import ThreadPoolExecutor
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

COOKIE_FILE = "modules/youtube_cookie.txt"   # اگر کوکی داری اینجا بزار

executor = ThreadPoolExecutor(max_workers=12)
track_store = {}


# ================================
#  جستجو SoundCloud
# ================================
def sc_search_sync(q):
    with yt_dlp.YoutubeDL({"quiet": True}) as y:
        return y.extract_info(f"scsearch10:{q}", download=False)


# ================================
#  دانلود سریع SoundCloud (بدون تبدیل)
# ================================
def sc_download_fast(url):
    opts = {
        "quiet": True,
        "format": "bestaudio/best",
        "concurrent_fragment_downloads": 10,
        "fragment_retries": 20,
        "retries": 20,
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    }
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)
        filename = y.prepare_filename(info)
    return info, filename


# ================================
#  fallback یوتیوب — ultra fast
# ================================
def yt_fast_sync(q):
    opts = {
        "quiet": True,
        "cookiefile": COOKIE_FILE,
        "format": "bestaudio/best",
        "concurrent_fragment_downloads": 10,
        "fragment_retries": 20,
        "retries": 20,
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    }
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(f"ytsearch1:{q}", download=True)
        if "entries" in info:
            info = info["entries"][0]
        filename = y.prepare_filename(info)
    return info, filename


# ================================
#   Handler — جستجو
# ================================
async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.strip()
    if not text.startswith("آهنگ "):
        return

    query = text.replace("آهنگ ", "").strip()
    msg = await update.message.reply_text("🔍 در حال جستجو در SoundCloud ...")

    loop = asyncio.get_running_loop()

    # جستجو SC
    try:
        sc = await loop.run_in_executor(executor, sc_search_sync, query)
    except:
        sc = None

    # اگر SC هیچی نبود → یوتیوب
    if not sc or "entries" not in sc or len(sc["entries"]) == 0:
        await msg.edit_text("❌ پیدا نشد — جستجو در یوتیوب...")

        info, file = await loop.run_in_executor(executor, yt_fast_sync, query)

        await msg.edit_text("⬇ ارسال...")
        await update.message.reply_audio(audio=open(file, "rb"), caption=f"🎵 {info['title']}")
        os.remove(file)
        return

    # اگر پیدا شد → لیست نشان بده
    entries = sc["entries"]
    track_store[update.effective_chat.id] = entries

    keyboard = [
        [InlineKeyboardButton(t["title"], callback_data=f"sc:{t['id']}")]
        for t in entries
    ]

    await msg.edit_text(
        f"🎵 {len(entries)} آهنگ پیدا شد — انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================================
#   Handler — انتخاب آهنگ
# ================================
async def music_select_handler(update, context: ContextTypes.DEFAULT_TYPE):

    cq = update.callback_query
    await cq.answer()

    chat_id = cq.message.chat_id
    track_id = cq.data.split(":")[1]

    tracks = track_store.get(chat_id, [])
    track = next((t for t in tracks if str(t["id"]) == track_id), None)

    if not track:
        return await cq.edit_message_text("❌ پیدا نشد.")

    await cq.edit_message_text("⬇ دانلود سریع...")

    loop = asyncio.get_running_loop()

    info, file = await loop.run_in_executor(
        executor, sc_download_fast, track["webpage_url"]
    )

    await context.bot.send_audio(chat_id, open(file, "rb"), caption=f"🎵 {info['title']}")

    os.remove(file)
    await cq.message.delete()
