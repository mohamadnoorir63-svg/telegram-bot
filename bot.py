# -*- coding: utf-8 -*-
import telebot
from telebot import types
from datetime import datetime
import re

# ================== تنظیمات ==================
TOKEN   = "7462131830:AAEGzgbjETaf3eukzGHW613i4y61Cs7lzTE"
SUDO_ID = 7089376754  # سودوی ربات (فقط این آیدی همه‌کاره است)
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
# ============================================

HELP_TEXT = """
📖 لیست دستورات:

⏰ ساعت | 📅 تاریخ | 📊 آمار | 🆔 ایدی
🔒 قفل لینک / باز کردن لینک
🧷 قفل استیکر / باز کردن استیکر
🤖 قفل ربات / باز کردن ربات
🚫 قفل تبچی / باز کردن تبچی
🔐 قفل گروه / باز کردن گروه
🚫 بن / ✅ حذف بن (ریپلای)
🔕 سکوت / 🔊 حذف سکوت (ریپلای)
⚠️ اخطار (ریپلای) → بعد از ۳ بار اخطار: بن
👑 مدیر / ❌ حذف مدیر (ریپلای)
📌 پن / ❌ حذف پن (ریپلای)
📋 لیست مدیران گروه
📋 لیست مدیران ربات
🎉 خوشامد روشن / خاموش
✍️ خوشامد متن [متن دلخواه]
🖼 ثبت عکس (روی عکس ریپلای کن و بفرست: ثبت عکس)
🧹 پاکسازی (حذف ۵۰ پیام آخر)
📢 ارسال (فقط سودو)
🛠 وضعیت ربات
🚪 لفت بده (فقط سودو)
"""

# ذخیره گروه‌ها
joined_groups = set()

@bot.my_chat_member_handler()
def track_groups(upd):
    try:
        chat = upd.chat
        if chat and chat.type in ("group", "supergroup"):
            joined_groups.add(chat.id)
    except:
        pass

# تابع کمکی
def is_admin(chat_id, user_id):
    if user_id == SUDO_ID:
        return True
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator", "creator")
    except:
        return False

# ========= دستورات پایه =========
@bot.message_handler(func=lambda m: m.text == "راهنما")
def help_cmd(m): bot.reply_to(m, HELP_TEXT)

@bot.message_handler(func=lambda m: m.text == "ساعت")
def time_cmd(m): bot.reply_to(m, f"⏰ ساعت: {datetime.now().strftime('%H:%M:%S')}")

@bot.message_handler(func=lambda m: m.text == "تاریخ")
def date_cmd(m): bot.reply_to(m, f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d')}")

@bot.message_handler(func=lambda m: m.text == "ایدی")
def id_cmd(m): bot.reply_to(m, f"🆔 آیدی شما: <code>{m.from_user.id}</code>\n🆔 آیدی گروه: <code>{m.chat.id}</code>")

@bot.message_handler(func=lambda m: m.text == "آمار")
def stats(m):
    try: count = bot.get_chat_member_count(m.chat.id)
    except: count = "نامشخص"
    bot.reply_to(m, f"📊 اعضای گروه: {count}")

# ========= سیستم اخطار =========
warnings = {}  # {chat_id: {user_id: count}}

@bot.message_handler(func=lambda m: m.reply_to_message and m.text == "اخطار")
def warn_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    user_id = m.reply_to_message.from_user.id
    chat_id = m.chat.id
    if chat_id not in warnings: warnings[chat_id] = {}
    if user_id not in warnings[chat_id]: warnings[chat_id][user_id] = 0
    warnings[chat_id][user_id] += 1
    count = warnings[chat_id][user_id]

    if count >= 3:
        try:
            bot.ban_chat_member(chat_id, user_id)
            bot.reply_to(m, f"🚫 کاربر <code>{user_id}</code> به دلیل ۳ بار اخطار بن شد.")
            warnings[chat_id][user_id] = 0
        except:
            bot.reply_to(m, "❗ نتوانستم بن کنم.")
    else:
        bot.reply_to(m, f"⚠️ کاربر <code>{user_id}</code> اخطار گرفت. ({count}/3)")

# ========= بقیه دستورات (بن، سکوت، مدیر، پین و ...) همون نسخه‌ی توست =========
# ========= RUN =========
print("🤖 Bot is running...")
bot.infinity_polling()
