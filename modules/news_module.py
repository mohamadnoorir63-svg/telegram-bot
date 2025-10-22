import requests
from bs4 import BeautifulSoup
import datetime
import asyncio
import os
from telegram import Update
from telegram.ext import ContextTypes

# 🌐 تابع گرفتن اخبار فارسی از گوگل‌نیوز
def fetch_persian_news(query="اخبار ایران"):
    try:
        # آدرس جستجوی گوگل‌نیوز برای فارسی
        url = f"https://news.google.com/rss/search?q={query}+when:1d&hl=fa&gl=IR&ceid=IR:fa"
        response = requests.get(url)
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "xml")

        items = soup.find_all("item")
        news_list = []
        for item in items[:5]:
            title = item.title.text
            link = item.link.text
            pub_date = item.pubDate.text
            news_list.append((title, link, pub_date))

        return news_list
    except Exception as e:
        print("❌ خطا در دریافت اخبار:", e)
        return []


# 📢 دستور دستی در ربات: /اخبار یا اخبار سیاسی و...
async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.replace("اخبار", "").strip() or "ایران"
    news = fetch_persian_news(query)

    if not news:
        await update.message.reply_text("⚠️ خبری یافت نشد، لطفاً دوباره تلاش کنید یا موضوع دیگری بنویسید.")
        return

    msg = f"🗞 <b>آخرین خبرهای {query}</b>:\n\n"
    for title, link, pub in news:
        msg += f"🔹 <b>{title}</b>\n🔗 {link}\n🕘 {pub}\n\n"

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    msg += f"🕓 زمان به‌روزرسانی: {now}"

    await update.message.reply_html(msg)


# ⏰ ارسال خودکار خبر داغ ساعت ۹ صبح
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
