# -*- coding: utf-8 -*-
import re
import telebot
from telebot import types

# ====== تنظیمات ======
TOKEN = "7462131830:AAEGzgbjETaf3eukzGHW613i4y61Cs7lzTE"
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ذخیره قفل‌ها
locks = {}

def is_admin(chat_id, user_id):
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator", "creator")
    except:
        return False

# ====== دستورات ======
@bot.message_handler(func=lambda m: m.text == "ایدی")
def cmd_id(m):
    bot.reply_to(m, f"🆔 آیدی شما: <code>{m.from_user.id}</code>\n"
                    f"🆔 آیدی گروه: <code>{m.chat.id}</code>")

@bot.message_handler(func=lambda m: m.text == "آمار")
def cmd_stats(m):
    try:
        cnt = bot.get_chat_member_count(m.chat.id)
    except:
        cnt = "نامشخص"
    bot.reply_to(m, f"👥 تعداد اعضای گروه: <b>{cnt}</b>")

@bot.message_handler(func=lambda m: m.text == "قفل لینک")
def lock_links(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    locks[m.chat.id] = True
    bot.reply_to(m, "🔒 لینک‌ها قفل شدند.")

@bot.message_handler(func=lambda m: m.text == "باز کردن لینک")
def unlock_links(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    locks[m.chat.id] = False
    bot.reply_to(m, "🔓 لینک‌ها آزاد شدند.")

# حذف لینک‌ها وقتی قفل فعاله
@bot.message_handler(content_types=['text'])
def check_links(m):
    if locks.get(m.chat.id) and not is_admin(m.chat.id, m.from_user.id):
        if re.search(r"(https?://|t\.me/)", m.text, re.I):
            try:
                bot.delete_message(m.chat.id, m.message_id)
            except:
                pass

print("🤖 Bot is running...")
bot.infinity_polling()
