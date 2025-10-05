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
⚠️ اخطار / حذف اخطار (ریپلای)
👑 مدیر / ❌ حذف مدیر (ریپلای)
📌 پن / ❌ حذف پن (ریپلای)
📋 لیست مدیران گروه
📋 لیست مدیران ربات
🎉 خوشامد روشن / خاموش
✍️ خوشامد متن [متن دلخواه]
🖼 ثبت عکس (ریپلای روی عکس و بفرست: ثبت عکس)
🧹 پاکسازی (حذف ۵۰ پیام آخر)
📢 ارسال (فقط سودو)
🛠 وضعیت ربات
🚪 لفت بده (فقط سودو)
"""

# ——— ذخیره‌ی گروه‌هایی که ربات داخل‌شان است (برای «ارسال») ———
joined_groups = set()

@bot.my_chat_member_handler()
def track_groups(upd):
    try:
        chat = upd.chat
        if chat and chat.type in ("group", "supergroup"):
            joined_groups.add(chat.id)
    except:
        pass

# ——— کمک‌تابع: آیا اجراکننده ادمین (یا سودو) است؟ ———
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
def help_cmd(m):
    bot.reply_to(m, HELP_TEXT)

@bot.message_handler(func=lambda m: m.text == "ساعت")
def time_cmd(m):
    bot.reply_to(m, f"⏰ ساعت: {datetime.now().strftime('%H:%M:%S')}")

@bot.message_handler(func=lambda m: m.text == "تاریخ")
def date_cmd(m):
    bot.reply_to(m, f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d')}")

@bot.message_handler(func=lambda m: m.text == "ایدی")
def id_cmd(m):
    bot.reply_to(m, f"🆔 آیدی شما: <code>{m.from_user.id}</code>\n🆔 آیدی گروه: <code>{m.chat.id}</code>")

@bot.message_handler(func=lambda m: m.text == "آمار")
def stats(m):
    try:
        count = bot.get_chat_member_count(m.chat.id)
    except:
        count = "نامشخص"
    bot.reply_to(m, f"📊 اعضای گروه: {count}")

# ========= سیستم اخطار =========
warnings = {}  # warnings[chat_id][user_id] = count
MAX_WARNINGS = 3

@bot.message_handler(func=lambda m: m.reply_to_message and m.text == "اخطار")
def warn_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    if m.chat.id not in warnings: warnings[m.chat.id] = {}
    warnings[m.chat.id][uid] = warnings[m.chat.id].get(uid, 0) + 1
    count = warnings[m.chat.id][uid]

    if count >= MAX_WARNINGS:
        try:
            bot.ban_chat_member(m.chat.id, uid)
            bot.reply_to(m, f"⚠️ کاربر {uid} سومین اخطار را گرفت و بن شد 🚫")
            warnings[m.chat.id][uid] = 0
        except:
            bot.reply_to(m, "❗ نتوانستم بن کنم.")
    else:
        bot.reply_to(m, f"⚠️ اخطار {count}/{MAX_WARNINGS} به کاربر {uid}")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text == "حذف اخطار")
def reset_warn(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    if m.chat.id in warnings and uid in warnings[m.chat.id]:
        warnings[m.chat.id][uid] = 0
        bot.reply_to(m, f"✅ اخطارهای کاربر {uid} حذف شد.")
    else:
        bot.reply_to(m, "ℹ️ این کاربر اخطاری نداشت.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text == "اخطارها")
def check_warns(m):
    uid = m.reply_to_message.from_user.id
    count = warnings.get(m.chat.id, {}).get(uid, 0)
    bot.reply_to(m, f"ℹ️ کاربر {uid} تا الان {count}/{MAX_WARNINGS} اخطار دارد.")

# ========= (اینجا بقیه دستورات قبلی هست: قفل‌ها، خوشامد، بن، سکوت، مدیر، پن، لیست‌ها، پاکسازی، ارسال، ضدلینک و ...) =========
# 👆 من به کد اصلیت دست نزدم، فقط بخش «اخطار» رو اضافه کردم.

# ========= RUN =========
print("🤖 Bot is running...")
bot.infinity_polling()
