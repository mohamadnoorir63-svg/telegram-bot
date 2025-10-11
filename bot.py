import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from pydub import AudioSegment

# توکن ربات تلگرام
BOT_TOKEN = os.getenv("BOT_TOKEN")

# کلید RapidAPI
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

# URL پایه RapidAPI
API_URL = "https://youtube-search-and-download.p.rapidapi.com/video/download"

HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "youtube-search-and-download.p.rapidapi.com"
}

# ✅ تابع جستجو و دانلود
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    await update.message.reply_text("🔍 در حال جست‌وجو و دانلود از یوتیوب... لطفاً صبر کنید ⏳")

    # مرحله ۱: جستجوی ویدیو در RapidAPI
    search_url = "https://youtube-search-and-download.p.rapidapi.com/search"
    search_params = {"query": query}
    response = requests.get(search_url, headers=HEADERS, params=search_params)
    data = response.json()

    if "contents" not in data or len(data["contents"]) == 0:
        await update.message.reply_text("❌ ویدیو پیدا نشد.")
        return

    video_id = data["contents"][0]["video"]["videoId"]

    # مرحله ۲: گرفتن لینک دانلود
    download_params = {"id": video_id}
    download_response = requests.get(API_URL, headers=HEADERS, params=download_params)
    download_info = download_response.json()

    if "url" not in download_info:
        await update.message.reply_text("⚠️ خطا در دریافت لینک دانلود.")
        return

    video_url = download_info["url"]

    # مرحله ۳: دانلود کامل ویدیو با stream=True
    try:
        video_response = requests.get(video_url, stream=True)
        with open("temp_video.mp4", "wb") as f:
            for chunk in video_response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در دانلود ویدیو: {e}")
        return

    # مرحله ۴: تبدیل ویدیو به MP3 با ffmpeg
    try:
        audio = AudioSegment.from_file("temp_video.mp4", format="mp4")
        audio.export("output.mp3", format="mp3")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در تبدیل به MP3: {e}")
        return

    # مرحله ۵: ارسال آهنگ به کاربر
    try:
        await update.message.reply_audio(audio=open("output.mp3", "rb"), title=query)
        os.remove("temp_video.mp4")
        os.remove("output.mp3")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در ارسال فایل: {e}")

# ✅ تابع شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام 👋 من ربات دانلود موزیک از یوتیوب هستم 🎵 فقط اسم آهنگ رو بفرست!")

# راه‌اندازی ربات
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
