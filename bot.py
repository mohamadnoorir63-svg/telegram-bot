import os
import requests
from pydub import AudioSegment
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
    await update.message.reply_text("🎵 اسم آهنگ یا لینک یوتیوب رو بفرست تا برات به MP3 تبدیل کنم 🎧")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text="🔎 در حال جست‌وجو و دانلود از یوتیوب... ⏳")

    try:
        # جستجوی ویدیو
        search_res = requests.get(SEARCH_URL, headers=HEADERS, params={"query": query, "type": "v"}).json()
        video_id = search_res["contents"][0]["video"]["videoId"]
        title = search_res["contents"][0]["video"]["title"]

        # دانلود ویدیو
        download_res = requests.get(DOWNLOAD_URL, headers=HEADERS, params={"id": video_id}).json()
        video_url = download_res.get("url")

        if not video_url:
            await context.bot.send_message(chat_id=chat_id, text="⚠️ لینک دانلود پیدا نشد.")
            return

        video_file = f"{title}.mp4"
        audio_file = f"{title}.mp3"

        video_data = requests.get(video_url)
        with open(video_file, "wb") as f:
            f.write(video_data.content)

        # تبدیل mp4 به mp3
        sound = AudioSegment.from_file(video_file, format="mp4")
        sound.export(audio_file, format="mp3")

        # ارسال صدا
        await context.bot.send_audio(chat_id=chat_id, audio=open(audio_file, "rb"), title=title)

        # پاکسازی فایل‌ها
        os.remove(video_file)
        os.remove(audio_file)

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"⚠️ خطا: {e}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🎧 Bot is running...")
    app.run_polling()
