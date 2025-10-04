import telebot
from telebot import types
import datetime

# توکن جدید
TOKEN = "7462131830:AAENzKipQzuxQ4UYkl9vcVgmmfDMKMUvZi8"
bot = telebot.TeleBot(TOKEN)

# دستور /start
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔐 قفل لینک", "🔓 باز کردن لینک")
    markup.add("🚫 بن", "🔇 سکوت")
    markup.add("👮 مدیر", "🆔 ایدی")
    markup.add("📊 آمار", "📖 راهنما")
    markup.add("⏰ ساعت", "📅 تاریخ")
    bot.send_message(message.chat.id, "به ربات مدیریت گروه خوش آمدی 🌹", reply_markup=markup)

# قفل لینک
@bot.message_handler(func=lambda m: m.text == "🔐 قفل لینک")
def lock_links(message):
    bot.send_message(message.chat.id, "✅ لینک‌ها قفل شدند.")

# باز کردن لینک
@bot.message_handler(func=lambda m: m.text == "🔓 باز کردن لینک")
def unlock_links(message):
    bot.send_message(message.chat.id, "✅ لینک‌ها باز شدند.")

# بن
@bot.message_handler(func=lambda m: m.text == "🚫 بن")
def ban_user(message):
    bot.send_message(message.chat.id, "🚫 کاربر بن شد (نمونه).")

# سکوت
@bot.message_handler(func=lambda m: m.text == "🔇 سکوت")
def mute_user(message):
    bot.send_message(message.chat.id, "🔇 کاربر سکوت شد (نمونه).")

# مدیر
@bot.message_handler(func=lambda m: m.text == "👮 مدیر")
def admins(message):
    bot.send_message(message.chat.id, "👮 لیست مدیران نمایش داده می‌شود (نمونه).")

# ایدی
@bot.message_handler(func=lambda m: m.text == "🆔 ایدی")
def user_id(message):
    bot.send_message(message.chat.id, f"🆔 ایدی شما: {message.from_user.id}")

# آمار
@bot.message_handler(func=lambda m: m.text == "📊 آمار")
def stats(message):
    bot.send_message(message.chat.id, "📊 آمار گروه: نمونه تستی.")

# راهنما
@bot.message_handler(func=lambda m: m.text == "📖 راهنما")
def help(message):
    text = """
📖 راهنما:
🔐 قفل لینک / 🔓 باز کردن لینک  
🚫 بن / 🔇 سکوت  
👮 مدیر / 🆔 ایدی  
📊 آمار / 📖 راهنما  
⏰ ساعت / 📅 تاریخ
"""
    bot.send_message(message.chat.id, text)

# ساعت
@bot.message_handler(func=lambda m: m.text == "⏰ ساعت")
def clock(message):
    now = datetime.datetime.now().strftime("%H:%M:%S")
    bot.send_message(message.chat.id, f"⏰ ساعت الان: {now}")

# تاریخ
@bot.message_handler(func=lambda m: m.text == "📅 تاریخ")
def date_today(message):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    bot.send_message(message.chat.id, f"📅 تاریخ امروز: {today}")

# اجرای ربات
bot.infinity_polling()
