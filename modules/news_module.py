import os, requests, asyncio
from datetime import datetime, timedelta, timezone
from telegram import Update
from telegram.ext import ContextTypes

API_KEY = os.getenv("NEWS_API_KEY", "demo")  # 🔑 اینو با کلید واقعی عوض کن

async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت خبرهای داغ روز"""
    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={API_KEY}"
    resp = requests.get(url).json()

    if resp.get("status") != "ok":
        return await update.message.reply_text("⚠️ خطا در دریافت خبرها یا API Key اشتباه است.")

    articles = resp.get("articles", [])[:5]
    if not articles:
        return await update.message.reply_text("😕 هیچ خبری یافت نشد.")

    msg = "🗞 <b>خبرهای داغ امروز:</b>\n\n"
    for art in articles:
        title = art.get("title", "—")
        url = art.get("url", "")
        msg += f"• <a href='{url}'>{title}</a>\n\n"

    await update.message.reply_text(msg, parse_mode="HTML")


# ======================= ⏰ ارسال خودکار هر روز ۹ صبح =======================
async def start_daily_news_scheduler(bot):
    while True:
        now = datetime.now(timezone.utc)
        target = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if now > target:
            target += timedelta(days=1)
        wait_time = (target - now).total_seconds()
        await asyncio.sleep(wait_time)

        try:
            await bot.send_message(
                chat_id=int(os.getenv("ADMIN_ID", "7089376754")),
                text="🗞 <b>خبرهای امروز آماده‌اند! بنویس «اخبار» تا ببینی 🔥</b>",
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"[News Scheduler Error] {e}")
