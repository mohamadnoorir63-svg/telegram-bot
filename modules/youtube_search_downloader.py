# modules/youtube_search_downloader.py
import os
import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes

# مسیر کوکی یوتیوب (همونی که خودت ساختی)
COOKIE_FILE = "modules/youtube_cookie.txt"

# پوشه دانلود
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


async def youtube_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # متن پیام کاربر
    query = (update.message.text or "").strip()

    # فقط وقتی کاربر دنبال آهنگ باشد:
    # مثال‌ها:
    #   دانلود آهنگ مهرداد جم شمال
    #   اهنگ مهرداد جم شمال
    #   آهنگ مهرداد جم شمال
    if not (
        query.startswith("دانلود آهنگ")
        or query.startswith("اهنگ")
        or query.startswith("آهنگ")
    ):
        return

    # حذف کلمه‌های شروع
    search_text = (
        query.replace("دانلود آهنگ", "")
        .replace("اهنگ", "")
        .replace("آهنگ", "")
        .strip()
    )

    if len(search_text) < 2:
        await update.message.reply_text("❌ لطفاً نام آهنگ یا خواننده را بنویس.")
        return

    msg = await update.message.reply_text(
        f"🎧 در حال جستجو در یوتیوب برای:\n🔎 <b>{search_text}</b>",
        parse_mode="HTML",
    )

    # ============================
    # 1️⃣ جستجو در یوتیوب
    # ============================
    search_url = f"ytsearch1:{search_text}"

    ydl_opts = {
        "quiet": True,
        "cookiefile": COOKIE_FILE,          # استفاده از کوکی‌های خودت
        "format": "bestaudio/best",         # ✅ اگر فقط صوت نبود، از best استفاده کن
        "noplaylist": True,
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
        "postprocessors": [                 # بعد از دانلود، تبدیل به MP3
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_url, download=True)

            # اگر نتیجه جستجو لیست بود، اولین مورد را بگیر
            if "entries" in info:
                info = info["entries"][0]

            # نام فایل اصلی قبل از تبدیل (مثلاً .webm)
            original_filename = ydl.prepare_filename(info)
            base, _ = os.path.splitext(original_filename)
            mp3_file = base + ".mp3"

        title = info.get("title", "Music")

        if not os.path.exists(mp3_file):
            await msg.edit_text("❌ دانلود انجام شد ولی فایل MP3 پیدا نشد.")
            return

        await msg.edit_text("⬇ در حال ارسال فایل صوتی...")

        with open(mp3_file, "rb") as f:
            await update.message.reply_audio(
                audio=f,
                title=title,
                caption=f"🎵 {title}",
            )

        # پاک کردن فایل‌ها
        try:
            if os.path.exists(original_filename):
                os.remove(original_filename)
        except:
            pass

        try:
            if os.path.exists(mp3_file):
                os.remove(mp3_file)
        except:
            pass

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود:\n{e}")
