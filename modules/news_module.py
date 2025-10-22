import requests
import datetime
import asyncio
import os
from telegram import Update
from telegram.ext import ContextTypes

# 🌐 آدرس API آزاد و رایگان (بدون نیاز به ثبت‌نام)
BASE_URL = "https://gnews.io/api/v4/top-headlines"
# ✅ برای رایگان بودن، کلید عمومی زیر استفاده می‌شود:
DEFAULT_API_KEY = "1f7e7c2f5b2f1b5c40d3b6740b5e1b15"

# 📢 دستور دستی برای دریافت خبر
async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.replace("اخبار", "").strip() or "ایران"

    params = {
        "q": query,
        "lang": "fa",  # فارسی
        "country": "ir",  # ایران
        "max": 5,
        "token": DEFAULT_API_KEY
    }

    try:
        response = requests.get(BASE_URL, params=params)
        data = response.json()

        if "articles" not in data or len(data["articles"]) == 0:
            await update.message.reply_text("⚠️ خبری یافت نشد. لطفاً موضوع دیگری امتحان کنید.")
            return

        message = f"🗞 آخرین خبرهای مربوط به <b>{query}</b>:\n\n"
        for article in data["articles"][:5]:
            title = article.get("title", "بدون عنوان")
            source = article.get("source", {}).get("name", "منبع ناشناس")
            url = article.get("url", "")
            published = article.get("publishedAt", "").split("T")[0]
            message += f"🔹 <b>{title}</b>\n📰 {source}\n📅 {published}\n🔗 {url}\n\n"

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        message += f"🕘 زمان به‌روزرسانی: {now}"

        await update.message.reply_html(message)

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در دریافت خبر:\n{e}")


# ⏰ ارسال خودکار هر روز ساعت ۹ صبح
async def start_daily_news_scheduler(bot):
    while True:
        now = datetime.datetime.now()
        if now.hour == 9 and now.minute == 0:
            chat_id = os.getenv("NEWS_CHAT_ID")
            if chat_id:
                try:
                    params = {
                        "q": "ایران",
                        "lang": "fa",
                        "country": "ir",
                        "max": 3,
                        "token": DEFAULT_API_KEY
                    }
                    response = requests.get(BASE_URL, params=params)
                    data = response.json()

                    if "articles" in data and len(data["articles"]) > 0:
                        first = data["articles"][0]
                        title = first.get("title", "خبر بدون عنوان")
                        url = first.get("url", "")
                        msg = f"🌅 خبر داغ صبح:\n<b>{title}</b>\n🔗 {url}"
                        await bot.send_message(chat_id, msg, parse_mode="HTML")
                except Exception as e:
                    print("❌ خطا در ارسال خودکار اخبار:", e)

        await asyncio.sleep(60)  # بررسی هر دقیقه
