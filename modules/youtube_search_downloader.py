# modules/youtube_search_downloader.py
import os
import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes

# مسیر فایل کوکی که خودت داخلش قرار می‌دهی
COOKIE_FILE = "modules/youtube_cookie.txt"

# پوشه دانلود
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


async def youtube_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = (update.message.text or "").strip()

    # فقط برای درخواست های آهنگ
    if not (
        query.startswith("دانلود آهنگ")
        or query.startswith("اهنگ")
        or query.startswith("آهنگ")
    ):
        return

    # متن جستجو
    search_text = (
        query.replace("دانلود آهنگ", "")
        .replace("اهنگ", "")
        .replace("آهنگ", "")
        .strip()
    )

    if len(search_text) < 2:
        return await update.message.reply_text("❌ لطفاً نام آهنگ را بنویس.")

    msg = await update.message.reply_text(f"🎧 جستجو در یوتیوب برای:\n🔎 {search_text}")

    # لینک جستجو در یوتیوب
    search_url = f"ytsearch1:{search_text}"

    # ================================
    # ⚡ تنظیمات پایدار yt-dlp فقط صوتی
    # ================================
    ydl_opts = {
        "quiet": True,
        "cookiefile": COOKIE_FILE,
        "format": "bestaudio/best",  # فقط صوت
        "noplaylist": True,
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",

        # جلوگیری از فرمت‌های خراب
        "prefer_ffmpeg": True,
        "cachedir": False,

        # تبدیل خودکار به MP3 پایدار
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],

        # حل مشکل signature solver
        "extractor_args": {
            "youtube": {
                "player_skip": ["js"],
            }
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_url, download=True)

            if "entries" in info:  
                info = info["entries"][0]

            base_filename = ydl.prepare_filename(info).rsplit(".", 1)[0]
            mp3_file = base_filename + ".mp3"

        title = info.get("title", "Music")

        await msg.edit_text("⬇ ارسال فایل صوتی...")

        with open(mp3_file, "rb") as f:
            await update.message.reply_audio(
                audio=f,
                title=title,
                caption=f"🎵 {title}",
            )

        # پاکسازی تمام فایل‌های اضافی
        for ext in [".mp3", ".webm", ".m4a"]:
            f = base_filename + ext
            if os.path.exists(f):
                os.remove(f)

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود:\n{e}")
