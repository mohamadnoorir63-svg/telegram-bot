# modules/youtube_search_downloader.py
import os
import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes

COOKIE_FILE = "modules/youtube_cookie.txt"
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


async def youtube_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = (update.message.text or "").strip()

    if not (
        query.startswith("دانلود آهنگ")
        or query.startswith("اهنگ")
        or query.startswith("آهنگ")
    ):
        return

    search_text = (
        query.replace("دانلود آهنگ", "")
        .replace("اهنگ", "")
        .replace("آهنگ", "")
        .strip()
    )

    msg = await update.message.reply_text(
        f"🎧 جستجو در یوتیوب برای:\n🔎 <b>{search_text}</b>",
        parse_mode="HTML"
    )

    search_url = f"ytsearch1:{search_text}"

    ydl_opts = {
        "cookiefile": COOKIE_FILE,

        # 🔥 فرار از SABR (خیلی مهم)
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios"]   # بهترین کلاینت برای صوت
            }
        },

        "quiet": True,
        "format": "bestaudio/best",
        "noplaylist": True,
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",

        # تبدیل خودکار به mp3
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_url, download=True)

            if "entries" in info:
                info = info["entries"][0]

            base = ydl.prepare_filename(info).rsplit(".", 1)[0]
            mp3_file = base + ".mp3"

        title = info.get("title", "Music")

        await msg.edit_text("⬇ در حال ارسال فایل صوتی...")

        with open(mp3_file, "rb") as f:
            await update.message.reply_audio(
                audio=f,
                caption=f"🎵 {title}",
                title=title,
            )

        # پاکسازی
        for fn in os.listdir(DOWNLOAD_FOLDER):
            if fn.startswith(info["id"]):
                os.remove(os.path.join(DOWNLOAD_FOLDER, fn))

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود:\n{e}")
