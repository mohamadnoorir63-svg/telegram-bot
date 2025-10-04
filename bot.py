import telebot

# توکن ربات
TOKEN = "7462131830:AAENzKipQzuxQ4UYkl9vcVgmmfDMKMUvZi8"
bot = telebot.TeleBot(TOKEN)

# وقتی کاربر دستور /start رو بزنه
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام 👋 ربات روشنه!")

# اجرای همیشگی ربات
bot.infinity_polling()
