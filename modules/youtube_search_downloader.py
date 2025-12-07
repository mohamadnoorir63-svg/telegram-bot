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
        f"🎧 جستجو در یوتیوب…\n🔎 <b>{search_text}</b>",
        parse_mode="HTML",
    )

    search_url = f"ytsearch1:{search_text}"

    # -------------------------------
    #  ⚡ نسخه بدون خطا و سریع
    # -------------------------------
    ydl_opts = {
        "quiet": True,
        "cookiefile": COOKIE_FILE,
        "format": "bestaudio/best",
        "noplaylist": True,
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        # حل خطاهای signature و فرمت
        "extractor_args": {
            "youtube": {
                "player_client": ["web", "android", "ios"]
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_url, download=True)

            if "entries" in info:
                info = info["entries"][0]

            base = os.path.splitext(ydl.prepare_filename(info))[0]
            mp3_file = base + ".mp3"

        title = info.get("title", "Music")

        await msg.edit_text("⬇ ارسال فایل صوتی…")

        with open(mp3_file, "rb") as f:
            await update.message.reply_audio(
                audio=f,
                title=title,
                caption=f"🎵 {title}",
            )

        # پاکسازی
        try:
            for ext in [".webm", ".m4a", ".mp4"]:
                temp = base + ext
                if os.path.exists(temp):
                    os.remove(temp)
        except:
            pass

        if os.path.exists(mp3_file):
            os.remove(mp3_file)

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود:\n{e}")
