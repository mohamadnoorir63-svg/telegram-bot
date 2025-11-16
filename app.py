from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Dispatcher
import os
import logging

TOKEN = os.environ.get("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, None)

app = Flask(__name__)

# فقط برای Webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dp.process_update(update)  # می‌تونی Handlerهای کوچک هم اضافه کنی
    return "OK", 200

# کاهش logging برای Heroku
logging.getLogger().setLevel(logging.WARNING)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
