import telebot
import os
import json
from telebot import types

# گرفتن توکن و آیدی مدیر از محیط سرور (Render)
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUDO_ID = int(os.getenv("SUDO_ID"))

bot = telebot.TeleBot(BOT_TOKEN)

# مسیر فایل دیتا
DATA_FILE = "data.json"

# اگر فایل وجود نداشت، می‌سازیمش
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"users": []}, f)

# تابع برای ذخیره کاربران جدید
def add_user(user_id):
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    if user_id not in data["users"]:
        data["users"].append(user_id)
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)

# استارت
@bot.message_handler(commands=['start'])
def start(message):
    add_user(message.chat.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📢 درباره ربات", "👤 تماس با ادمین")
    bot.reply_to(message, "سلام 👋\nبه ربات خوش اومدی 🌸", reply_markup=markup)

# دکمه‌ها
@bot.message_handler(func=lambda m: True)
def menu(message):
    if message.text == "📢 درباره ربات":
        bot.reply_to(message, "من یه ربات ساده ولی قوی هستم 😎 ساخته شده توسط ادمین ❤️")
    elif message.text == "👤 تماس با ادمین":
        bot.reply_to(message, f"برای ارتباط با ادمین به آیدی زیر پیام بده:\n\n`{SUDO_ID}`", parse_mode="Markdown")
    elif message.text.startswith("/bc") and message.chat.id == SUDO_ID:
        text = message.text.replace("/bc", "").strip()
        if text:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
            for uid in data["users"]:
                try:
                    bot.send_message(uid, f"📢 پیام جدید از ادمین:\n\n{text}")
                except:
                    pass
            bot.reply_to(message, "✅ پیام به همه کاربران ارسال شد.")
        else:
            bot.reply_to(message, "❗ بعد از دستور /bc متن پیام رو بنویس.")
    else:
        bot.reply_to(message, "😅 دستور ناشناخته‌ست. از منو استفاده کن.")

bot.polling(non_stop=True)
