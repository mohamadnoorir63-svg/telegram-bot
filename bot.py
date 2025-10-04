# -*- coding: utf-8 -*-
import telebot
from telebot import types
from datetime import datetime
import re

# ==================
TOKEN = "7462131830:AAEGzgbjETaf3eukzGHW613i4y61Cs7lzTE"
SUDO_ID = 7089376754  # آیدی عددی شما
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
# ==================

HELP_TEXT = """
📖 لیست دستورات:

⏰ ساعت | 📅 تاریخ | 📊 آمار | 🆔 ایدی
🔒 قفل لینک / باز کردن لینک
🧷 قفل استیکر / باز کردن استیکر
🤖 قفل ربات / باز کردن ربات
🚫 قفل تبچی / باز کردن تبچی
🔐 قفل گروه / باز کردن گروه
🎙 قفل ویس / باز کردن ویس
🎵 قفل موزیک / باز کردن موزیک
🚫 بن / ✅ حذف بن (ریپلای)
🔕 سکوت / 🔊 حذف سکوت (ریپلای)
👑 مدیر / ❌ حذف مدیر (ریپلای)
📌 پن (ریپلای) / حذف پن
🎉 خوشامد روشن / خاموش
✍️ خوشامد متن [متن دلخواه]
🖼 ثبت عکس (ریپلای روی عکس و بفرست: ثبت عکس)
🧹 پاکسازی (حذف ۵۰ پیام آخر)
📢 ارسال (فقط سودو)
🛠 وضعیت ربات
🚪 لفت بده (فقط سودو)
"""

# ذخیره‌ی گروه‌ها
joined_groups = set()

@bot.my_chat_member_handler()
def track_groups(update):
    chat = update.chat
    if chat and chat.type in ("group","supergroup"):
        joined_groups.add(chat.id)

def is_admin(chat_id, user_id):
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator","creator") or user_id == SUDO_ID
    except:
        return False

# ========= پنل مدیریتی (فقط سودو در پیوی) =========
@bot.message_handler(commands=['start'])
def start_msg(m):
    if m.from_user.id == SUDO_ID and m.chat.type == "private":
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("📊 آمار گروه‌ها","📢 ارسال همگانی")
        kb.add("🛠 وضعیت ربات","❌ بستن پنل")
        bot.send_message(m.chat.id,"👑 پنل مدیریتی سودو",reply_markup=kb)
    else:
        bot.send_message(m.chat.id,"سلام! من آماده‌ام 🌹")

@bot.message_handler(func=lambda m: m.chat.type=="private" and m.from_user.id==SUDO_ID and m.text=="📊 آمار گروه‌ها")
def panel_stats(m):
    txt = f"📊 تعداد گروه‌هایی که ربات داخل‌شان است: <b>{len(joined_groups)}</b>"
    bot.reply_to(m,txt)

@bot.message_handler(func=lambda m: m.chat.type=="private" and m.from_user.id==SUDO_ID and m.text=="📢 ارسال همگانی")
def panel_broadcast(m):
    bot.reply_to(m,"📨 متن یا عکس خود را بفرستید تا برای همه گروه‌ها ارسال شود.")
    waiting_broadcast[m.from_user.id]=True

@bot.message_handler(func=lambda m: m.chat.type=="private" and m.from_user.id==SUDO_ID and m.text=="🛠 وضعیت ربات")
def panel_status(m):
    try:
        me_id = bot.get_me().id
        lines=[]
        for gid in joined_groups:
            cm = bot.get_chat_member(gid, me_id)
            lines.append(f"🔹 گروه {gid} → {cm.status}")
        bot.reply_to(m,"🛠 وضعیت ربات:\n"+"\n".join(lines[:20])) # تا 20 گروه
    except:
        bot.reply_to(m,"❗ نتوانستم وضعیت را بگیرم.")

@bot.message_handler(func=lambda m: m.chat.type=="private" and m.from_user.id==SUDO_ID and m.text=="❌ بستن پنل")
def close_panel(m):
    bot.send_message(m.chat.id,"پنل بسته شد ❌",reply_markup=types.ReplyKeyboardRemove())

# ========= پخش پیام همگانی =========
waiting_broadcast = {}
@bot.message_handler(func=lambda m: m.from_user.id==SUDO_ID and waiting_broadcast.get(m.from_user.id))
def do_broadcast(m):
    waiting_broadcast[m.from_user.id]=False
    success=0
    for gid in list(joined_groups):
        try:
            if m.content_type=="text":
                bot.send_message(gid, m.text)
            elif m.content_type=="photo":
                bot.send_photo(gid, m.photo[-1].file_id, caption=m.caption or "")
            success+=1
        except: pass
    bot.reply_to(m,f"✅ پیام به {success} گروه ارسال شد.")

# ========= بقیه دستورات (مثل نسخه قبل) =========
# اینجا همون کدهای قبلی: خوشامد، قفل‌ها، بن/سکوت، پن، پاکسازی، ضد لینک و ... 
# (همون‌هایی که در آخرین نسخه کاملت بودن) 👇
# ...
# ========= RUN =========
print("🤖 Bot is running...")
bot.infinity_polling()
