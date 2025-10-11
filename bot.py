# -- coding: utf-8 --
import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# 📦 گرفتن متغیرها از تنظیمات Heroku
BOT_TOKEN = os.getenv("BOT_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

# 🌐 تنظیمات RapidAPI
API_URL = "https://youtube-video-fast-downloader24.p.rapidapi.com/download"
API_HOST = "youtube-video-fast-downloader24.p.rapidapi.com"

# 🎬 فرمان /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🎵 <b>سلام!</b>\n"
        "من یه ربات جستجوگر و دانلود موزیک هستم 🎧\n\n"
        "کافیه اسم آهنگ یا لینک یوتیوب رو بفرستی تا برات بیارم 🎶\n\n"
        "مثلاً:\n"
        "<code>شادمهر عقیلی خسته شدم</code>\n"
        "یا لینک:\n"
        "<code>https://www.youtube.com/watch?v=JGwWNGJdvx8</code>"
    )
    await update.message.reply_text(text, parse_mode="HTML")

# 🔍 بررسی پیام‌ها
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    await update.message.reply_text("🔎 در حال پردازش درخواست... لطفاً صبر کن ⏳")

    try:
        # اگر لینک YouTube بود
        if "youtube.com" in query or "youtu.be" in query:
            url = f"{API_URL}?url={query}"
            headers = {
                "x-rapidapi-key": RAPIDAPI_KEY,
                "x-rapidapi-host": API_HOST
            }

            response = requests.get(url, headers=headers, timeout=15)
            data = response.json()

            if "link" in data and data["link"]:
                mp3_url = data["link"]

                # دانلود فایل موقت
                audio_data = requests.get(mp3_url)
                temp_file = "temp.mp3"
                with open(temp_file, "wb") as f:
                    f.write(audio_data.content)

                # ارسال فایل صوتی به کاربر
                await update.message.reply_audio(
                    audio=open(temp_file, "rb"),
                    caption="🎧 آهنگ آماده است! از شنیدنش لذت ببر ❤️"
                )

                # حذف فایل موقت
                os.remove(temp_file)
            else:
                await update.message.reply_text("❗ خطا در دریافت آهنگ. لطفاً لینک دیگری امتحان کن 🎶")

        # اگر فقط اسم آهنگ فرستاده شده
        else:
            yt_search = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            await update.message.reply_text(
                f"🎶 متاسفانه API فقط با لینک مستقیم کار می‌کند.\n"
                f"🔗 برای دانلود، وارد لینک زیر شو و یکی از ویدیوها را انتخاب کن:\n{yt_search}\n\n"
                "سپس لینک آن ویدیو را برای من بفرست 😊"
            )

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطایی رخ داد:\n{str(e)}")

# 🚀 اجرای ربات
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Music Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
