from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Dispatcher
import os
import logging
import requests

# -------------------------
# تنظیمات اصلی
# -------------------------
TOKEN = os.environ.get("TOKEN")  # توکن ربات در Config Vars Heroku
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, None)       # فقط Webhook، Handlerها در bot.py

# -------------------------
# Flask Webhook
# -------------------------
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    """دریافت پیام از Telegram و ارسال به Dispatcher"""
    update = Update.de_json(request.get_json(force=True), bot)
    dp.process_update(update)  # Dispatcher سبک فقط پیام‌ها را پاس می‌دهد
    return "OK", 200

# -------------------------
# کاهش مصرف منابع Heroku
# -------------------------
logging.getLogger().setLevel(logging.WARNING)

# -------------------------
# HTTP Keep-Alive برای سرعت
# -------------------------
session = requests.Session()
bot._request = bot._request.__class__(bot.token, session=session)

# -------------------------
# اجرا روی Heroku
# -------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
