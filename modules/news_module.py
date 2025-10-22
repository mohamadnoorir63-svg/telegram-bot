import requests
from bs4 import BeautifulSoup
import datetime
import asyncio
import os
from telegram import Update
from telegram.ext import ContextTypes
from newspaper import Article  # ✅ برای گرفتن متن و خلاصه خبر

# 🌍 گرفتن اخبار فارسی از Google News
def fetch_persian_news(query="اخبار ایران"):
    urls = [
        f"https://news.google.com/rss/search?q={query}+when:1d&hl=fa&gl=IR&ceid=IR:fa",
        f"https://news.google.com/rss/search?q={query}+when:1d&hl=fa&gl=AF&ceid=AF:fa",
    ]

    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.text, "xml")
            items = soup.find_all("item")
            if items:
                news_list = []
                for item in items[:5]:  # فقط ۵ تا خبر جدید
                    title = item.title.text
                    link = item.link.text
                    pub_date = item.pubDate.text
                    news_list.append((title, link, pub_date))
                return news_list
        except Exception as e:
            print("❌ خطا در دریافت از:", url, "|", e)
            continue
    return []


# ✍️ خلاصه‌سازی از لینک خبر
def summarize_article(url):
    try:
        article = Article(url, language='fa')
        article.download()
        article.parse()
        article.nlp()
        return article.summary if article.summary else article.text[:400]
    except Exception:
        return None


# 📢 فرمان ربات برای گرفتن خبر
async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.replace("اخبار", "").strip() or "ایران"
    news = fetch_persian_news(query)

    if not news:
        await update.message.reply_text("⚠️ خبری یافت نشد یا گوگل نیوز محدودیت داده است.")
        return

    msg = f"📰 <b>آخرین خبرهای {query}</b>\n\n"
    for title, link, pub in news:
        summary = summarize_article(link)
        msg += f"🗞 <b>{title}</b>\n"
        if summary:
            msg += f"{summary}\n"
        msg += f"🕒 {pub}\n\n"
        msg += "──────────────────────\n"

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    msg += f"📅 بروزرسانی: <i>{now}</i>"

    await update.message.reply_html(msg[:3900])


# ⏰ ارسال خودکار خبر داغ ساعت ۹ صبح
async def start_daily_news_scheduler(bot):
    while True:
        now = datetime.datetime.now()
        if now.hour == 9 and now.minute == 0:
            chat_id = os.getenv("NEWS_CHAT_ID")
            if chat_id:
                news = fetch_persian_news("خبر داغ ایران")
                if news:
                    first = news[0]
                    summary = summarize_article(first[1])
                    msg = f"🔥 <b>خبر داغ امروز:</b>\n\n🗞 {first[0]}\n\n{summary or 'خلاصه‌ای در دسترس نیست.'}"
                    await bot.send_message(chat_id, msg, parse_mode="HTML")
        await asyncio.sleep(60)
