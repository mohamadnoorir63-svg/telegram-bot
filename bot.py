import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from pydub import AudioSegment

# تنظیم مسیر ffmpeg در محیط Heroku
from pydub.utils import which
AudioSegment.converter = which("ffmpeg")
AudioSegment.ffprobe = which("ffprobe")

# گرفتن کلیدها از محیط
BOT_TOKEN = os.getenv("BOT_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

# آدرس‌های RapidAPI
SEARCH_URL = "https://youtube-search-and-download.p.rapidapi.com/search"
DOWNLOAD_URL = "https://youtube-search-and-download.p.rapidapi.com/video/download"

HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "youtube-search-and-download.p.rapidapi.com"
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎧 سلام! من ربات جستجو و دانلود آهنگ از یوتیوبم 🎶\n"
        "کافیه اسم آهنگ یا خواننده رو بفرستی تا برات به MP3 تبدیل کنم."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    chat_id = update.effective_chat.id

    await context.bot.send_message(chat_id=chat_id, text="🔎 در حال جست‌وجو در یوتیوب... لطفاً صبر کنید ⏳")

    try:
        # مرحله ۱: جستجوی ویدیو
        search_res = requests.get(SEARCH_URL, headers=HEADERS, params={"query": query, "type": "v"}).json()
        if not search_res.get("contents"):
            await context.bot.send_message(chat_id=chat_id, text="❌ ویدیویی با این نام پیدا نشد.")
            return

        video_id = search_res["contents"][0]["video"]["videoId"]
        title = search_res["contents"][0]["video"]["title"]

        # مرحله ۲: دریافت لینک دانلود از RapidAPI
        download_res = requests.get(DOWNLOAD_URL, headers=HEADERS, params={"id": video_id}).json()
        video_url = download_res.get("url")

        if not video_url:
            await context.bot.send_message(chat_id=chat_id, text="⚠️ لینک دانلود پیدا نشد.")
            return

        # مرحله ۳: دانلود کامل ویدیو با دنبال کردن redirect
        await context.bot.send_message(chat_id=chat_id, text="⬇️ در حال دانلود ویدیو از یوتیوب...")
        video_response = requests.get(video_url, stream=True, allow_redirects=True, timeout=120)

        total_size = 0
        with open("temp_video.mp4", "wb") as f:
            for chunk in video_response.iter_content(chunk_size=1024 * 64):
                if chunk:
                    f.write(chunk)
                    total_size += len(chunk)

        if total_size < 50000:
            await context.bot.send_message(chat_id=chat_id, text="⚠️ فایل ناقص دریافت شد، دوباره امتحان کن.")
            os.remove("temp_video.mp4")
            return

        # مرحله ۴: تبدیل به MP3 با ffmpeg/pydub
        await context.bot.send_message(chat_id=chat_id, text="🎶 در حال تبدیل به MP3...")
        sound = AudioSegment.from_file("temp_video.mp4", format="mp4")
        sound.export("output.mp3", format="mp3")

        # مرحله ۵: ارسال فایل نهایی
        await context.bot.send_audio(chat_id=chat_id, audio=open("output.mp3", "rb"), title=title)

        # مرحله ۶: پاکسازی فایل‌ها
        os.remove("temp_video.mp4")
        os.remove("output.mp3")

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"⚠️ خطا در پردازش: {e}")


if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🚀 Bot is running...")
    app.run_polling()
