import os
import requests
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# گرفتن کلید از هاست
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# آدرس API
API_URL = "https://youtube-search-and-download.p.rapidapi.com/video/download"

HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "youtube-search-and-download.p.rapidapi.com"
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎵 سلام! اسم آهنگ یا لینک یوتیوب رو بفرست تا برات دانلودش کنم.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    await update.message.reply_text("🔎 در حال جست‌وجو و پردازش... لطفاً صبر کنید ⏳")

    try:
        # مرحله ۱: جستجو ویدیو با اسم
        search_url = "https://youtube-search-and-download.p.rapidapi.com/search"
        search_query = {"query": query, "type": "v"}
        search_response = requests.get(search_url, headers=HEADERS, params=search_query)
        search_data = search_response.json()

        if not search_data.get("contents"):
            await update.message.reply_text("❌ آهنگی با این اسم پیدا نشد.")
            return

        video_id = search_data["contents"][0]["video"]["videoId"]

        # مرحله ۲: دریافت لینک دانلود
        download_query = {"id": video_id}
        download_response = requests.get(API_URL, headers=HEADERS, params=download_query)
        download_data = download_response.json()

        video_url = download_data["url"]

        # مرحله ۳: دانلود فایل
        video_content = requests.get(video_url)
        filename = f"{query}.mp4"

        with open(filename, "wb") as f:
            f.write(video_content.content)

        # مرحله ۴: ارسال ویدیو به کاربر
        await update.message.reply_video(video=open(filename, "rb"))
        os.remove(filename)

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در پردازش آهنگ: {str(e)}")


if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()
