# ======================= 📰 News Module — اخبار روز، خودکار و هوشمند =======================
import aiohttp
import openai
import os
import asyncio
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes

# ✅ کلید تست برای GNews (بدون ثبت‌نام)
NEWS_API_KEY = "1c8286a33f7e4f598f8df6bb7e2dc45e"

# ✅ از Heroku بخوان (کلید ChatGPT)
openai.api_key = os.getenv("OPENAI_API_KEY")

# ✅ شناسه مدیر اصلی برای ارسال خودکار اخبار (آیدی خودت)
ADMIN_ID = 123456789  # ← آیدی عددی خودت رو بزار اینجا

# 🌍 کشورها برای جستجو
COUNTRY_MAP = {
    "افغانستان": "af",
    "ایران": "ir",
    "امریکا": "us",
    "انگلستان": "gb",
    "جهان": "us"
}

async def summarize_text(text: str) -> str:
    """خلاصه و ترجمه فارسی متن خبر"""
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "تو یک مترجم و خلاصه‌ساز فارسی هستی."},
                {"role": "user", "content": f"این خبر را به فارسی خلاصه کن:\n{text}"}
            ],
            max_tokens=120
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "⚠️ ترجمه در دسترس نیست."

async def fetch_news(topic="general", country="ir"):
    """دریافت اخبار خام از GNews"""
    url = f"https://gnews.io/api/v4/top-headlines?lang=en&country={country}&topic={topic}&max=3&apikey={NEWS_API_KEY}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            return await res.json()

async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فرمان دستی برای دریافت خبر"""
    text = update.message.text.strip()

    # تشخیص کشور
    country = "ir"
    for name, code in COUNTRY_MAP.items():
        if name in text:
            country = code
            break

    # تشخیص دسته‌بندی
    if "سیاسی" in text:
        topic, title = "politics", "🗳 اخبار سیاسی"
    elif "ورزشی" in text:
        topic, title = "sports", "⚽️ اخبار ورزشی"
    elif "اقتصادی" in text:
        topic, title = "business", "💰 اخبار اقتصادی"
    else:
        topic, title = "general", "📰 سرخط خبرها"

    data = await fetch_news(topic, country)
    if not data.get("articles"):
        return await update.message.reply_text("😕 خبری یافت نشد.")

    msg = f"{title} ({text}):\n\n"
    for article in data["articles"]:
        title_text = article["title"]
        desc = article.get("description", "")
        url_link = article["url"]
        summary = await summarize_text(f"{title_text}\n{desc}")
        msg += f"🗞 <b>{title_text}</b>\n{summary}\n🔗 {url_link}\n\n"

    await update.message.reply_text(msg, parse_mode="HTML")


# ======================= 🕘 ارسال خودکار اخبار ساعت ۹ صبح =======================
async def send_daily_news(context: ContextTypes.DEFAULT_TYPE):
    """ارسال خودکار خبرها برای مدیر اصلی"""
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        data = await fetch_news("general", "ir")
        if not data.get("articles"):
            return
        msg = f"📰 <b>سرخط خبرهای امروز ({now})</b>\n\n"
        for article in data["articles"]:
            summary = await summarize_text(f"{article['title']}\n{article.get('description','')}")
            msg += f"🗞 <b>{article['title']}</b>\n{summary}\n🔗 {article['url']}\n\n"

        await context.bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode="HTML")
        print("✅ خبرهای روز با موفقیت برای مدیر ارسال شد.")
    except Exception as e:
        print(f"⚠️ خطا در ارسال خبر روزانه: {e}")


# ======================= ⏱ زمان‌بندی خودکار =======================
async def start_daily_news_scheduler(application):
    """زمان‌بندی خودکار برای ۹ صبح هر روز"""
    while True:
        now = datetime.now()
        next_run = (now.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1))
        wait_seconds = (next_run - now).total_seconds()
        await asyncio.sleep(wait_seconds)
        await send_daily_news(application)
