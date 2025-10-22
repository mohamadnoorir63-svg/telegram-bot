import requests
from bs4 import BeautifulSoup
import datetime
import asyncio
import os
from telegram import Update
from telegram.ext import ContextTypes

# 🌍 تابع گرفتن خبر از Google News RSS (بدون API)
def fetch_persian_news(query="اخبار ایران"):
    urls = [
        f"https://news.google.com/rss/search?q={query}+when:1d&hl=fa&gl=IR&ceid=IR:fa",
        f"https://news.google.com/rss/search?q={query}+when:1d&hl=fa&gl=US&ceid=US:fa",
        f"https://news.google.com/rss/search?q={query}+when:1d&hl=fa&gl=AF&ceid=AF:fa"
    ]

    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.text, "xml")
            items = soup.find_all("item")
            if items:
                news_list = []
                for item in items[:5]:
                    title = item.title.text
                    link = item.link.text
                    pub_date = item.pubDate.text
                    news_list.append((title, link, pub_date))
                return news_list
        except Exception as e:
            print("❌ خطا در دریافت از:", url, "|", e)
            continue
    return []


# 📰 فرمان در ربات — وقتی بنویسی "اخبار" یا "اخبار ورزشی"
async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.replace("اخبار", "").strip() or "ایران"
    news = fetch_persian_news(query)

    if not news:
        await update.message.reply_text("⚠️ خبری یافت نشد یا گوگل نیوز محدودیت داده. بعداً دوباره امتحان کن.")
        return

    msg = f"🗞 <b>آخرین خبرهای {query}</b>\n\n"
    for title, link, pub in news:
        msg += f"🔹 <b>{title}</b>\n🔗 {link}\n🕘 {pub}\n\n"

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    msg += f"🕓 بروزرسانی: {now}"

    await update.message.reply_html(msg)


# ⏰ ارسال خودکار خبر داغ هر روز ساعت ۹ صبح
async def start_daily_news_scheduler(bot):
    while True:
        now = datetime.datetime.now()
        if now.hour == 9 and now.minute == 0:
            chat_id = os.getenv("NEWS_CHAT_ID")
            if chat_id:
                news = fetch_persian_news("خبر داغ")
                if news:
                    first = news[0]
                    msg = f"🌅 <b>خبر داغ امروز:</b>\n\n{first[0]}\n🔗 {first[1]}"
                    await bot.send_message(chat_id, msg, parse_mode="HTML")
        await asyncio.sleep(60)
