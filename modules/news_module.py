import requests
import asyncio
import datetime
from telegram import Update
from telegram.ext import ContextTypes

import os

# 🔑 دریافت کلید از تنظیمات Heroku
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# 🌍 آدرس پایه NewsAPI
BASE_URL = "https://newsapi.org/v2/top-headlines"

# 🇮🇷 کشور پیش‌فرض
COUNTRY = "ir"


async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش خبرها بر اساس دستور کاربر"""
    if not NEWS_API_KEY:
        await update.message.reply_text("⚠️ کلید API برای دریافت خبرها تنظیم نشده است.")
        return

    query = update.message.text.replace("اخبار", "").strip()
    category = "general"

    # 🎯 تشخیص نوع دسته‌بندی
    if "ورزش" in query:
        category = "sports"
    elif "اقتصاد" in query:
        category = "business"
    elif "سیاست" in query or "سیاسی" in query:
        category = "politics"
    elif "علم" in query:
        category = "science"
    elif "فناوری" in query:
        category = "technology"
    elif "سلامت" in query:
        category = "health"

    # 🔗 درخواست از API
    url = f"{BASE_URL}?country={COUNTRY}&category={category}&apiKey={NEWS_API_KEY}"

    try:
        response = requests.get(url)
        data = response.json()

        if data.get("status") != "ok" or not data.get("articles"):
            await update.message.reply_text("⚠️ خبری یافت نشد یا API محدودیت دارد.")
            return

        # 🗞 ساخت متن نهایی خبرها
        message = f"🗞 خبرهای داغ امروز ({category}):\n\n"
        for article in data["articles"][:5]:
            title = article.get("title", "بدون عنوان")
            source = article.get("source", {}).get("name", "نامشخص")
            url = article.get("url", "")
            message += f"🔹 <b>{title}</b>\n📰 منبع: {source}\n🔗 {url}\n\n"

        today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        message += f"📅 به‌روزرسانی: {today}"

        await update.message.reply_html(message)

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در دریافت خبرها:\n{e}")


# ⏰ زمان‌بندی ارسال خودکار خبر
async def start_daily_news_scheduler(bot):
    """ارسال خودکار خبرها ساعت ۹ صبح"""
    while True:
        now = datetime.datetime.now()
        # بررسی زمان (۹ صبح)
        if now.hour == 9 and now.minute == 0:
            chat_id = os.getenv("NEWS_CHAT_ID")  # آیدی گروه یا PV
            if chat_id:
                url = f"{BASE_URL}?country={COUNTRY}&apiKey={NEWS_API_KEY}"
                response = requests.get(url)
                data = response.json()

                if data.get("articles"):
                    top_news = data["articles"][0]
                    title = top_news.get("title", "")
                    source = top_news.get("source", {}).get("name", "")
                    news_url = top_news.get("url", "")
                    msg = f"🌅 خبر ویژه صبح:\n\n<b>{title}</b>\n📰 {source}\n🔗 {news_url}"
                    await bot.send_message(chat_id=chat_id, text=msg, parse_mode="HTML")

        # بررسی هر 60 ثانیه
        await asyncio.sleep(60)
