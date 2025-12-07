# modules/youtube_search_downloader.py
import os
import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes

COOKIE_FILE = "modules/youtube_cookie.txt"
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# ================================
#  🎵 دانلود فقط صوتی — نسخه ضد خطا
# ================================
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
        f"🎧 جستجو در یوتیوب...\n🔎 <b>{search_text}</b>", parse_mode="HTML"
    )

    search_url = f"ytsearch1:{search_text}"

    # ============================
    # 🎼 نسخه ضد خطا
    # ============================
    ydl_opts = {
        "quiet": True,
        "cookiefile": COOKIE_FILE,

        # ⛔ هیچ فرمت خاصی انتخاب نکن → خودش هر فرمت صوتی موجود را می‌گیرد
        "format": "bestaudio/best",

        "noplaylist": True,
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",

        # 🔥 تبدیل خودکار به mp3 (بدون توجه به پسوند دانلود شده)
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],

        # مشکل SABR را دور می‌زند
        "extractor_args": {
            "youtube": {
                "player_client": ["android"],
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_url, download=True)

            if "entries" in info:
                info = info["entries"][0]

            base_path = ydl.prepare_filename(info).rsplit(".", 1)[0]
            mp3_file = base_path + ".mp3"

        title = info.get("title", "Music")

        await msg.edit_text("⬇ ارسال فایل صوتی...")

        with open(mp3_file, "rb") as f:
            await update.message.reply_audio(
                audio=f,
                caption=f"🎵 {title}",
                title=title,
            )

        # پاکسازی
        for ext in [".webm", ".m4a", ".mp3"]:
            f = base_path + ext
            if os.path.exists(f):
                try:
                    os.remove(f)
                except:
                    pass

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود:\n{e}")
