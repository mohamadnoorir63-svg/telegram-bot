import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

API_URL = "https://youtube-search-and-download.p.rapidapi.com/video/download"
HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "youtube-search-and-download.p.rapidapi.com"
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎵 سلام! اسم آهنگ یا لینک یوتیوب رو بفرست تا برات دانلودش کنم.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    chat_id = update.effective_chat.id

    await context.bot.send_message(chat_id=chat_id, text="🔎 در حال جست‌وجو و پردازش... لطفاً صبر کنید ⏳")

    try:
        # جست‌وجوی ویدیو
        search_url = "https://youtube-search-and-download.p.rapidapi.com/search"
        search_query = {"query": query, "type": "v"}
        search_response = requests.get(search_url, headers=HEADERS, params=search_query)
        search_data = search_response.json()

        if not search_data.get("contents"):
            await context.bot.send_message(chat_id=chat_id, text="❌ آهنگی با این اسم پیدا نشد.")
            return

        video_id = search_data["contents"][0]["video"]["videoId"]

        # دریافت لینک دانلود
        download_query = {"id": video_id}
        download_response = requests.get(API_URL, headers=HEADERS, params=download_query)
        download_data = download_response.json()

        video_url = download_data["url"]

        # دانلود فایل
        video_content = requests.get(video_url)
        filename = f"{query}.mp4"
        with open(filename, "wb") as f:
            f.write(video_content.content)

        # ارسال ویدیو
        await context.bot.send_video(chat_id=chat_id, video=open(filename, "rb"))
        os.remove(filename)

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"⚠️ خطا در پردازش آهنگ: {e}")


if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Bot is running...")
    app.run_polling()
