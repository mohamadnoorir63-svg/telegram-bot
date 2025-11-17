# ==============================
# app.py — Fast Heroku Webhook
# ==============================

from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application
import os
import threading

# -------------------------
# 1) TOKEN از Config Vars
# -------------------------

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ خطا: BOT_TOKEN در Heroku تنظیم نشده!")

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  
# مثل: https://mybot2.herokuapp.com/webhook

if not WEBHOOK_URL:
    raise ValueError("❌ WEBHOOK_URL در Heroku تنظیم نشده!")

# -------------------------
# 2) ساخت Bot + Application
# -------------------------

bot = Bot(token=TOKEN)

application = Application.builder() \
    .token(TOKEN) \
    .concurrent_updates(True) \
    .build()

# -------------------------
# 3) بارگذاری Handlerها
# -------------------------

from bot import register_handlers
register_handlers(application)

# -------------------------
# 4) Webhook با Flask
# -------------------------

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "🤖 Bot is running!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, bot)

        # پیام می‌رود داخل صف — فوق سریع
        application.update_queue.put_nowait(update)

    except Exception as e:
        print("❌ Webhook Error:", e)
        return "Error", 500

    return "OK", 200


# -------------------------
# 5) اجرای Application در Thread جدا
# -------------------------

def run_application():
    application.run_polling(stop_signals=None)

threading.Thread(target=run_application, daemon=True).start()

# -------------------------
# 6) اجرای Flask روی Heroku
# -------------------------

if __name__ == "__main__":
    print("🚀 Starting Fast Webhook Server...")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
