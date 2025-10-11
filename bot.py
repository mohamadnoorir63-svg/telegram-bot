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
    await update.message.reply_text("🎶 سلام! اسم آهنگ یا لینک یوتیوب رو بفرست تا فایل صوتی‌ش رو برات بفرستم.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text="🔎 در حال جست‌وجو و تبدیل به MP3... لطفاً صبر کنید ⏳")

    try:
        # جستجوی ویدیو
        search_response = requests.get(SEARCH_URL, headers=HEADERS, params={"query": query, "type": "v"})
        search_data = search_response.json()

        if not search_data.get("contents"):
            await context.bot.send_message(chat_id=chat_id, text="❌ آهنگی با این نام پیدا نشد.")
            return

        video_id = search_data["contents"][0]["video"]["videoId"]
        title = search_data["contents"][0]["video"]["title"]

        # دانلود صدا
        download_response = requests.get(DOWNLOAD_URL, headers=HEADERS, params={"id": video_id})
        download_data = download_response.json()

        # پیدا کردن لینک mp3 از پاسخ
        audio_url = None
        for fmt in download_data.get("formats", []):
            if fmt.get("mimeType", "").startswith("audio/mp4") or fmt.get("mimeType", "").startswith("audio/mp3"):
                audio_url = fmt.get("url")
                break

        if not audio_url:
            audio_url = download_data.get("url")  # بک‌آپ

        if not audio_url:
            await context.bot.send_message(chat_id=chat_id, text="⚠️ لینک دانلود صوت پیدا نشد.")
            return

        # دانلود فایل از لینک واقعی
        audio_content = requests.get(audio_url)
        filename = f"{title}.mp3"

        if len(audio_content.content) < 500:
            await context.bot.send_message(chat_id=chat_id, text="⚠️ فایل صوتی خالی بود یا کامل دانلود نشد.")
            return

        with open(filename, "wb") as f:
            f.write(audio_content.content)

        # ارسال فایل صوتی
        await context.bot.send_audio(chat_id=chat_id, audio=open(filename, "rb"), title=title)
        os.remove(filename)

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"⚠️ خطا در دانلود: {e}")


if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🎵 Bot is running...")
    app.run_polling()
