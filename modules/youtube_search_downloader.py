import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes

# ================================
SUDO_USERS = [8588347189]
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

executor = ThreadPoolExecutor(max_workers=4)  # افزایش سرعت با چند Thread

# ================================
# دانلود ویدیو یا صوت
# ================================
def _download_file(url, audio_only=False):
    opts = {
        "format": "bestaudio/best" if audio_only else "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "noprogress": True,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
        "concurrent_fragment_downloads": 16,
    }
    if audio_only:
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if audio_only:
            filename = filename.rsplit(".", 1)[0] + ".mp3"
    return info, filename

# ================================
# هندلر دانلود
# ================================
async def download_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    url = update.message.text.strip()
    chat_id = update.effective_chat.id

    # محدودیت در گروه
    if update.effective_chat.type != "private":
        user = update.effective_user
        if user.id not in SUDO_USERS:
            return

    msg = await update.message.reply_text("⬇ در حال دانلود ...")

    loop = asyncio.get_running_loop()
    # مشخص کنید صوت یا ویدیو
    audio_only = False  # True برای MP3

    try:
        info, filename = await loop.run_in_executor(executor, _download_file, url, audio_only)

        await msg.edit_text("⬇ در حال ارسال فایل ...")
        # ارسال با send_document (پشتیبانی تا 2 گیگ)
        sent = await context.bot.send_document(
            chat_id,
            open(filename, "rb"),
            caption=info.get("title", "File")
        )

    except Exception as e:
        await msg.edit_text(f"❌ خطا: {e}")
        return

    finally:
        if os.path.exists(filename):
            os.remove(filename)
        await msg.delete()
