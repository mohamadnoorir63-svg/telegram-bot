# modules/filmefarsi_downloader.py
import os
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor

import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes

# ============================
#  تنظیمات اولیه
# ============================

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

COOKIE_FILE = "modules/filmefarsi_cookie.txt"

# اگر کوکی وجود ندارد → فایل درست کن
os.makedirs("modules", exist_ok=True)
if not os.path.exists(COOKIE_FILE):
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        f.write("# Paste filmefarsi.com cookies here (Netscape Format)\n")

# فقط لینک‌های سایت خودت
SITE_RE = re.compile(r"(https?://(?:www\.)?filmefarsi\.com[^\s]+)")

executor = ThreadPoolExecutor(max_workers=4)


# ============================
# تابع سینک برای دانلود بدون هنگ
# ============================
def _download_filmefarsi_sync(url):
    """
    دانلود از filmefarsi.com با سرعت بالا و استفاده از کوکی‌ها
    """
    ydl_opts = {
        "cookiefile": COOKIE_FILE,  # ← کوکی سایت خودت
        "quiet": True,
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(title)s.%(ext)s",
        "noplaylist": True,
        "concurrent_fragment_downloads": 5,  # سرعت بالا
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)

    return info, file_path


# ============================
# هندلر اصلی دانلود
# ============================
async def filmefarsi_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    match = SITE_RE.search(text)

    if not match:
        return  # اگر لینک مربوط به filmefarsi نبود → بی‌خیال

    url = match.group(1)

    msg = await update.message.reply_text("📥 در حال دانلود از FilmeFarsi...")

    loop = asyncio.get_running_loop()

    try:
        info, file_path = await loop.run_in_executor(
            executor,
            _download_filmefarsi_sync,
            url
        )
    except Exception as e:
        return await msg.edit_text(f"❌ خطا در دانلود:\n{e}")

    title = info.get("title", "Video")

    await msg.edit_text("⬇ در حال ارسال فایل...")

    # ارسال فایل ویدیو
    try:
        await update.message.reply_video(
            video=open(file_path, "rb"),
            caption=f"🎬 {title}"
        )
    except Exception as e:
        await msg.edit_text(f"❌ خطا در ارسال فایل:\n{e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
