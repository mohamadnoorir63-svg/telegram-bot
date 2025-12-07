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

    if len(search_text) < 2:
        return await update.message.reply_text("❌ لطفاً نام آهنگ را بنویس.")

    msg = await update.message.reply_text(
        f"🎧 جستجو در یوتیوب...\n🔎 <b>{search_text}</b>",
        parse_mode="HTML"
    )

    search_url = f"ytsearch1:{search_text}"

    # ==============
    # 1️⃣ تلاش برای دانلود فقط صوت (M4A)
    # ==============
    ydl_audio_only = {
        "quiet": True,
        "cookiefile": COOKIE_FILE,
        "format": "bestaudio[ext=m4a]/bestaudio",
        "noplaylist": True,
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",

        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],

        "prefer_ffmpeg": True,
        "nocheckcertificate": True,
        "cachedir": False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_audio_only) as ydl:
            info = ydl.extract_info(search_url, download=True)

        if "entries" in info:
            info = info["entries"][0]

        base = ydl.prepare_filename(info).rsplit(".", 1)[0]
        mp3_file = base + ".mp3"

        if os.path.exists(mp3_file):
            await msg.edit_text("⬇ ارسال فایل صوتی...")
            with open(mp3_file, "rb") as f:
                await update.message.reply_audio(
                    audio=f,
                    caption=f"🎵 {info.get('title','Music')}",
                )
            os.remove(mp3_file)
            return

        # اگر به اینجا رسید، یعنی فایل صوتی مستقیم قابل دانلود نبود
    except:
        pass

    # ==============
    # 2️⃣ حالت دوم — ویدیو دانلود شود و صوت استخراج شود
    # ==============
    ydl_fallback = {
        "quiet": True,
        "cookiefile": COOKIE_FILE,
        "format": "best",
        "noplaylist": True,
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_fallback) as ydl:
            info = ydl.extract_info(search_url, download=True)

        if "entries" in info:
            info = info["entries"][0]

        video_file = ydl.prepare_filename(info)
        mp3_file = video_file.rsplit(".", 1)[0] + ".mp3"

        # استخراج صدا
        os.system(f'ffmpeg -i "{video_file}" -vn -ab 192k "{mp3_file}" -y')

        await msg.edit_text("⬇ ارسال فایل صوتی...")

        with open(mp3_file, "rb") as f:
            await update.message.reply_audio(
                audio=f,
                caption=f"🎵 {info.get('title','Music')}",
            )

        # پاکسازی
        if os.path.exists(video_file):
            os.remove(video_file)
        if os.path.exists(mp3_file):
            os.remove(mp3_file)

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود:\n{e}")  
