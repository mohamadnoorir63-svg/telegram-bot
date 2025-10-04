# -*- coding: utf-8 -*-
import telebot
import random

# --- توکن مستقیم ---
TOKEN = "7462131830:AAEGzgbjETaf3eukzGHW613i4y61Cs7lzTE"
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- جوک‌ها ---
jokes = [
    "یه روزی ربات بودم... بعد فهمیدم هنوزم رباتم! 🤖",
    "هیچ‌وقت به کامپیوترت اعتماد نکن، حتی وقتی میگه 'من هنگ نمی‌کنم' 😅",
    "می‌دونی چرا کتاب ریاضی ناراحته بود؟ چون پر از مشکل بود 📘😂",
]

# --- حقایق جالب ---
facts = [
    "زرافه‌ها تارهای صوتی ندارن! 🦒",
    "موز در واقع یک نوع توت هست 🍌",
    "حلزون می‌تونه تا ۳ سال بخوابه 😴🐌",
]

# --- دستورات ---
@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "سلام 😍 من ربات سرگرمی‌ام!\n"
                    "از این دستورها استفاده کن:\n"
                    "🎲 /dice - تاس بریز\n"
                    "😂 /joke - جوک\n"
                    "💡 /fact - حقیقت جالب\n"
                    "❤️ /love - درصد عشق")

@bot.message_handler(commands=['dice'])
def dice(m):
    n = random.randint(1, 6)
    bot.reply_to(m, f"🎲 تاس ریختی: <b>{n}</b>")

@bot.message_handler(commands=['joke'])
def joke(m):
    bot.reply_to(m, random.choice(jokes))

@bot.message_handler(commands=['fact'])
def fact(m):
    bot.reply_to(m, random.choice(facts))

@bot.message_handler(commands=['love'])
def love(m):
    percent = random.randint(0, 100)
    bot.reply_to(m, f"❤️ درصد عشق شما: <b>{percent}%</b> 😍")

print("🤖 Fun Bot is running...")
bot.infinity_polling()
