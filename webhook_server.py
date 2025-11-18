from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler
import os
import asyncio

# 🔹 توکن ربات (از Config Vars هروکو می‌خواند)
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(TOKEN)

# 🔹 ساخت اپلیکیشن تلگرام مستقل برای Webhook
application = ApplicationBuilder().token(TOKEN).build()

# ======================================================
# 🔹 Import handler های سبک و فوری از bot.py
# فقط handler های سبک مثل /start، /help، و دستورات فوری
from bot import start, toggle, help_command  # ← مطمئن شو این handler ها در bot.py موجودند

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("toggle", toggle))
application.add_handler(CommandHandler("help", help_command))
# می‌توانی دستورات فوری دیگر را هم اضافه کنی

# ======================================================
# 🔹 ساخت Flask app برای Webhook
app = Flask(__name__)

@app.post("/")
def webhook():
    """دریافت آپدیت از تلگرام و اضافه کردن به queue"""
    update = Update.de_json(request.get_json(force=True), bot)
    application.update_queue.put_nowait(update)
    return "OK", 200

# ======================================================
# 🔹 وظایف استارتاپ Webhook
async def on_startup(app):
    print("🌟 Webhook server آماده و فعال است!")

application.post_init = on_startup

# ======================================================
# 🔹 اجرای Flask روی Heroku
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
