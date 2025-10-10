import os
import time
import telebot

# توکن از متغیر محیطی
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN پیدا نشد! لطفاً در تنظیمات Render اضافه‌اش کن.")

bot = telebot.TeleBot(TOKEN)

# حذف وبهوک برای جلوگیری از خطای 409
bot.remove_webhook()

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "✅ ربات با موفقیت فعاله و آماده به کاره!")

@bot.message_handler(func=lambda m: True)
def echo(m):
    bot.reply_to(m, f"📩 پیامت دریافت شد:\n{m.text}")

while True:
    try:
        print("🤖 ربات در حال اجراست...")
        bot.polling(non_stop=True, interval=2)
    except Exception as e:
        print("⚠️ خطا:", e)
        time.sleep(5)
