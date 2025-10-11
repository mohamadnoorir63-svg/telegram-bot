import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os

# 🧩 دریافت متغیرها از تنظیمات هاست (Heroku Config Vars)
BOT_TOKEN = os.getenv("BOT_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

# 📦 مشخصات API RapidAPI (این قسمت رو اگر API دیگه‌ای داری می‌تونی عوض کنی)
API_URL = "https://youtube-video-fast-downloader24.p.rapidapi.com/download"
API_HOST = "youtube-video-fast-downloader24.p.rapidapi.com"


# 🎬 شروع ربات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎵 سلام! من ربات جستجوگر موزیک هستم.\n"
        "کافیه اسم آهنگ یا لینک یوتیوب رو بفرستی تا برات بفرستم 🎧\n\n"
        "✨ پشتیبانی از فارسی و انگلیسی ✅"
    )


# 🔍 تابع جستجوی موزیک
async def search_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()

    await update.message.reply_text(f"🔎 در حال جستجو برای '{query}' هستم...\n⏳ لطفاً صبر کن...")

    try:
        # اگر لینک یوتیوب بود
        if "youtube.com" in query or "youtu.be" in query:
            url = f"{API_URL}?url={query}"
        else:
            # اگر فقط اسم آهنگ بود → کاربر رو راهنمایی می‌کنیم تا لینک بفرسته
            yt_search = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            await update.message.reply_text(
                f"🎶 نتایج جستجو برای '{query}':\n\n🔗 {yt_search}\n"
                "لطفاً یکی از لینک‌های بالا رو کپی کرده و بفرست تا دانلود کنم 🎧"
            )
            return

        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": API_HOST
        }

        response = requests.get(url, headers=headers)
        data = response.json()

        if "link" in data and data["link"]:
            mp3_url = data["link"]
            await update.message.reply_audio(audio=mp3_url, caption=f"🎵 آهنگ {query}")
        else:
            await update.message.reply_text("❌ آهنگ پیدا نشد یا لینک معتبر نبود. لطفاً دوباره امتحان کن 🎧")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در دریافت آهنگ:\n{str(e)}")


# 🚀 اجرای ربات
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_music))

    print("🤖 ربات موزیک در حال اجراست...")
    app.run_polling()


if __name__ == "__main__":
    main()
