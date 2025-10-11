import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

SEARCH_URL = "https://youtube-search-and-download.p.rapidapi.com/search"
DOWNLOAD_URL = "https://youtube-search-and-download.p.rapidapi.com/video/download"

HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "youtube-search-and-download.p.rapidapi.com"
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎧 سلام! اسم آهنگ یا لینک یوتیوب رو بفرست تا فایل صوتی‌ش رو برات بفرستم 🎶")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text="🔎 در حال جست‌وجو و تبدیل به MP3... لطفاً صبر کنید ⏳")

    try:
        # جستجو در یوتیوب
        search_response = requests.get(SEARCH_URL, headers=HEADERS, params={"query": query, "type": "v"})
        data = search_response.json()

        if not data.get("contents"):
            await context.bot.send_message(chat_id=chat_id, text="❌ آهنگی با این نام پیدا نشد.")
            return

        video_id = data["contents"][0]["video"]["videoId"]

        # دریافت لینک دانلود (MP3)
        download_response = requests.get(DOWNLOAD_URL, headers=HEADERS, params={"id": video_id})
        download_data = download_response.json()

        if "url" not in download_data:
            await context.bot.send_message(chat_id=chat_id, text="⚠️ لینک دانلود پیدا نشد.")
            return

        audio_url = download_data["url"]
        audio_data = requests.get(audio_url)

        filename = f"{query}.mp3"
        with open(filename, "wb") as f:
            f.write(audio_data.content)

        # ارسال صوت به تلگرام
        await context.bot.send_audio(chat_id=chat_id, audio=open(filename, "rb"), title=query)
        os.remove(filename)

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"⚠️ خطا: {e}")


if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🎵 Bot is running...")
    app.run_polling()
