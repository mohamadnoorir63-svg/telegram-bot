from telebot import TeleBot, types
from datetime import datetime

# ربات با توکن تو
bot = TeleBot("7462131830:AAENzKipQzuxQ4UYkl9vcVgmmfDMKMUvZi8")

# لیست قفل‌ها
locks = {
    "link": False,
}

# دستور شروع
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("🔐 پنل مدیریت", callback_data="panel")
    markup.add(btn1)
    bot.reply_to(message, "سلام! ربات روشنه ✅", reply_markup=markup)

# وقتی روی دکمه پنل زد
@bot.callback_query_handler(func=lambda call: call.data == "panel")
def panel(call):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("🚫 قفل لینک", callback_data="lock_link")
    btn2 = types.InlineKeyboardButton("✅ باز کردن لینک", callback_data="unlock_link")
    markup.add(btn1, btn2)
    bot.edit_message_text("🔐 پنل مدیریت", call.message.chat.id, call.message.message_id, reply_markup=markup)

# قفل لینک
@bot.callback_query_handler(func=lambda call: call.data == "lock_link")
def lock_link(call):
    locks["link"] = True
    bot.answer_callback_query(call.id, "قفل لینک فعال شد 🚫")

# باز کردن لینک
@bot.callback_query_handler(func=lambda call: call.data == "unlock_link")
def unlock_link(call):
    locks["link"] = False
    bot.answer_callback_query(call.id, "قفل لینک غیرفعال شد ✅")

# حذف پیام‌های دارای لینک وقتی قفل فعاله
@bot.message_handler(func=lambda message: "http" in message.text.lower() if message.text else False)
def check_links(message):
    if locks["link"]:
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass

print("ربات روشن شد ✅")
bot.infinity_polling()
