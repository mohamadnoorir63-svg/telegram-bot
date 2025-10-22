# ======================= 📰 News Module — اخبار روز، سیاسی، ورزشی =======================
import aiohttp
from telegram import Update
from telegram.ext import ContextTypes
import os

# 🗝 API Key را از محیط (یا مستقیم) بگیر
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "اینجا_کلیدت_را_بگذار")

async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آخرین اخبار بر اساس موضوع"""
    text = update.message.text.strip()

    # 🔍 شناسایی نوع خبر
    if "سیاسی" in text:
        category = "politics"
        title = "🗳 اخبار سیاسی"
    elif "ورزشی" in text:
        category = "sports"
        title = "⚽️ اخبار ورزشی"
    elif "اقتصادی" in text:
        category = "business"
        title = "💰 اخبار اقتصادی"
    else:
        category = "general"
        title = "📰 اخبار عمومی امروز"

    url = f"https://newsapi.org/v2/top-headlines?language=fa&category={category}&pageSize=5&apiKey={NEWS_API_KEY}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as res:
                data = await res.json()
    except Exception as e:
        return await update.message.reply_text(f"⚠️ خطا در دریافت خبر:\n{e}")

    if data.get("status") != "ok" or not data.get("articles"):
        return await update.message.reply_text("😕 خبری یافت نشد!")

    msg = f"{title}:\n\n"
    for article in data["articles"][:5]:
        title = article.get("title", "")
        source = article.get("source", {}).get("name", "")
        url = article.get("url", "")
        msg += f"🗞 <b>{title}</b>\n🌐 {source}\n🔗 {url}\n\n"

    await update.message.reply_text(msg, parse_mode="HTML")
