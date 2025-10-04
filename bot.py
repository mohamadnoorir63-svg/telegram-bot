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

# ========= دستورات پایه =========
@bot.message_handler(func=lambda m: m.text=="ساعت")
def time_cmd(m): bot.reply_to(m, f"⏰ ساعت: {datetime.now().strftime('%H:%M:%S')}")

@bot.message_handler(func=lambda m: m.text=="تاریخ")
def date_cmd(m): bot.reply_to(m, f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d')}")

@bot.message_handler(func=lambda m: m.text=="ایدی")
def id_cmd(m): bot.reply_to(m, f"🆔 آیدی شما: <code>{m.from_user.id}</code>\n🆔 آیدی گروه: <code>{m.chat.id}</code>")

@bot.message_handler(func=lambda m: m.text=="آمار")
def stats(m):
    try: count = bot.get_chat_member_count(m.chat.id)
    except: count = "نامشخص"
    bot.reply_to(m, f"📊 اعضای گروه: {count}")

# ========= خوشامدگویی =========
welcome_enabled = {}
welcome_texts = {}
welcome_photos = {}

@bot.message_handler(content_types=['new_chat_members'])
def welcome(m):
    if not welcome_enabled.get(m.chat.id): return
    for u in m.new_chat_members:
        name = u.first_name
        txt = welcome_texts.get(m.chat.id, "خوش آمدی 🌹").replace("{name}", name)
        if m.chat.id in welcome_photos:
            bot.send_photo(m.chat.id, welcome_photos[m.chat.id], caption=txt)
        else:
            bot.send_message(m.chat.id, txt)

@bot.message_handler(func=lambda m: m.text=="خوشامد روشن")
def welcome_on(m):
    welcome_enabled[m.chat.id]=True
    bot.reply_to(m, "✅ خوشامد فعال شد.")

@bot.message_handler(func=lambda m: m.text=="خوشامد خاموش")
def welcome_off(m):
    welcome_enabled[m.chat.id]=False
    bot.reply_to(m, "❌ خوشامد خاموش شد.")

@bot.message_handler(func=lambda m: m.text and m.text.startswith("خوشامد متن"))
def welcome_text(m):
    txt = m.text.replace("خوشامد متن","",1).strip()
    welcome_texts[m.chat.id]=txt
    bot.reply_to(m, "✍️ متن خوشامد ذخیره شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="ثبت عکس")
def save_photo(m):
    if not m.reply_to_message.photo: return
    welcome_photos[m.chat.id] = m.reply_to_message.photo[-1].file_id
    bot.reply_to(m, "🖼 عکس خوشامد ذخیره شد.")

# ========= لفت بده =========
@bot.message_handler(func=lambda m: m.text=="لفت بده")
def leave_cmd(m):
    if m.from_user.id!=SUDO_ID: return
    bot.send_message(m.chat.id,"به دستور سودو خارج می‌شوم 👋")
    bot.leave_chat(m.chat.id)

# ========= قفل لینک =========
lock_links = {}

@bot.message_handler(func=lambda m: m.text=="قفل لینک")
def lock_links_cmd(m):
    lock_links[m.chat.id]=True
    bot.reply_to(m,"🔒 لینک‌ها قفل شدند.")

@bot.message_handler(func=lambda m: m.text=="باز کردن لینک")
def unlock_links_cmd(m):
    lock_links[m.chat.id]=False
    bot.reply_to(m,"🔓 لینک‌ها آزاد شدند.")

@bot.message_handler(content_types=['text'])
def anti_links(m):
    if lock_links.get(m.chat.id) and not m.from_user.id==SUDO_ID:
        if re.search(r"(t\.me|http)", m.text.lower()):
            try: bot.delete_message(m.chat.id, m.message_id)
            except: pass

# ========= مدیریت (بن / سکوت) =========
@bot.message_handler(func=lambda m: m.text=="بن" and m.reply_to_message)
def ban_user(m):
    try:
        bot.ban_chat_member(m.chat.id, m.reply_to_message.from_user.id)
        bot.reply_to(m,"⛔ کاربر بن شد.")
    except: bot.reply_to(m,"⚠️ خطا در بن کردن.")

@bot.message_handler(func=lambda m: m.text=="حذف بن" and m.reply_to_message)
def unban_user(m):
    try:
        bot.unban_chat_member(m.chat.id, m.reply_to_message.from_user.id)
        bot.reply_to(m,"✅ کاربر آزاد شد.")
    except: bot.reply_to(m,"⚠️ خطا در حذف بن.")

@bot.message_handler(func=lambda m: m.text=="سکوت" and m.reply_to_message)
def mute_user(m):
    try:
        bot.restrict_chat_member(m.chat.id, m.reply_to_message.from_user.id, types.ChatPermissions(can_send_messages=False))
        bot.reply_to(m,"🔇 کاربر سکوت شد.")
    except: bot.reply_to(m,"⚠️ خطا در سکوت کردن.")

@bot.message_handler(func=lambda m: m.text=="حذف سکوت" and m.reply_to_message)
def unmute_user(m):
    try:
        bot.restrict_chat_member(m.chat.id, m.reply_to_message.from_user.id, types.ChatPermissions(can_send_messages=True))
        bot.reply_to(m,"🔊 سکوت کاربر برداشته شد.")
    except: bot.reply_to(m,"⚠️ خطا در حذف سکوت.")

# ========= RUN =========
print("🤖 Bot is running...")
bot.infinity_polling()
