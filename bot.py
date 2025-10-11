# -- coding: utf-8 --
import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

# 📦 API‌ها
SEARCH_URL = "https://youtube-v31.p.rapidapi.com/search"
DOWNLOAD_URL = "https://youtube-video-fast-downloader24.p.rapidapi.com/download"
DOWNLOAD_HOST = "youtube-video-fast-downloader24.p.rapidapi.com"

# 🎬 شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎧 سلام! من ربات موزیک یاب هستم.\n"
        "اسم آهنگ یا لینک یوتیوب رو بفرست تا برات بیارم 🎶\n\n"
        "مثلاً:\n"
        "شادمهر خسته شدم\n"
        "یا لینک مستقیم یوتیوب"
    )

# 🔎 جستجو و دانلود
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    await update.message.reply_text("🔍 در حال جستجو و پردازش... لطفاً صبر کنید ⏳")

    try:
        # اگه لینک مستقیم فرستاده شده
        if "youtube.com" in query or "youtu.be" in query:
            await download_audio(update, query)
            return

        # جستجو در یوتیوب بر اساس اسم آهنگ
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "youtube-v31.p.rapidapi.com"
        }
        params = {"q": query, "part": "snippet", "maxResults": "1"}

        search = requests.get(SEARCH_URL, headers=headers, params=params, timeout=10)
        data = search.json()

        if "items" not in data or not data["items"]:
            await update.message.reply_text("❌ آهنگی با این اسم پیدا نشد.")
            return

        video_id = data["items"][0]["id"]["videoId"]
        title = data["items"][0]["snippet"]["title"]
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        await update.message.reply_text(f"🎵 پیدا شد!\n<b>{title}</b>\nدر حال دانلود...", parse_mode="HTML")
        await download_audio(update, video_url)

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطایی رخ داد:\n{str(e)}")

# 🎧 دانلود از یوتیوب
async def download_audio(update: Update, video_url):
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": DOWNLOAD_HOST
    }
    params = {"url": video_url}

    try:
        res = requests.get(DOWNLOAD_URL, headers=headers, params=params, timeout=15)
        data = res.json()

        if "link" in data and data["link"]:
            mp3_url = data["link"]
            # دانلود و ارسال
            audio_data = requests.get(mp3_url)
            temp_file = "temp.mp3"
            with open(temp_file, "wb") as f:
                f.write(audio_data.content)

            await update.message.reply_audio(
                audio=open(temp_file, "rb"),
                caption="🎶 آهنگ آماده است ❤️"
            )
            os.remove(temp_file)
        else:
            await update.message.reply_text("❗ خطا در دریافت آهنگ از سرور.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در دانلود:\n{str(e)}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Music Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
