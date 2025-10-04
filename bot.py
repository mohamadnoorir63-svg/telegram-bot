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
🎙 قفل ویس / باز کردن ویس
🎵 قفل موزیک / باز کردن موزیک
🤖 قفل ربات / باز کردن ربات
🚫 قفل تبچی / باز کردن تبچی
🔐 قفل گروه / باز کردن گروه
🚫 بن / ✅ حذف بن (ریپلای)
🔕 سکوت / 🔊 حذف سکوت (ریپلای)
📌 پین (ریپلای) / ❌ حذف پین (ریپلای)
👑 مدیر / ❌ حذف مدیر (ریپلای)
🎉 خوشامد روشن / خاموش
✍️ خوشامد متن [متن دلخواه]
🖼 ثبت عکس (ریپلای روی عکس و بفرست: ثبت عکس)
🧹 پاکسازی (حذف ۵۰ پیام آخر)
📢 ارسال (فقط سودو)
🛠 وضعیت ربات
🚪 لفت بده (فقط سودو)
"""

# ذخیره گروه‌ها
joined_groups = set()

@bot.my_chat_member_handler()
def track_groups(update):
    chat = update.chat
    if chat and chat.type in ("group","supergroup"):
        joined_groups.add(chat.id)

# ===== helper =====
def is_admin(chat_id, user_id):
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator","creator") or user_id == SUDO_ID
    except:
        return False

# ========= دستورات پایه =========
@bot.message_handler(func=lambda m: m.text=="راهنما")
def help_cmd(m): bot.reply_to(m, HELP_TEXT)

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
    for u in m.new_chat_members:
        if not welcome_enabled.get(m.chat.id): continue
        name = u.first_name or ""
        txt = welcome_texts.get(m.chat.id, "خوش آمدی 🌹").replace("{name}", name)
        if m.chat.id in welcome_photos:
            bot.send_photo(m.chat.id, welcome_photos[m.chat.id], caption=txt)
        else:
            bot.send_message(m.chat.id, txt)

@bot.message_handler(func=lambda m: m.text=="خوشامد روشن")
def welcome_on(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    welcome_enabled[m.chat.id]=True
    bot.reply_to(m, "✅ خوشامد فعال شد.")

@bot.message_handler(func=lambda m: m.text=="خوشامد خاموش")
def welcome_off(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    welcome_enabled[m.chat.id]=False
    bot.reply_to(m, "❌ خوشامد خاموش شد.")

@bot.message_handler(func=lambda m: m.text and m.text.startswith("خوشامد متن"))
def welcome_text(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    txt = m.text.replace("خوشامد متن","",1).strip()
    welcome_texts[m.chat.id]=txt
    bot.reply_to(m, "✍️ متن خوشامد ذخیره شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="ثبت عکس")
def save_photo(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    if not m.reply_to_message.photo: return
    welcome_photos[m.chat.id] = m.reply_to_message.photo[-1].file_id
    bot.reply_to(m, "🖼 عکس خوشامد ذخیره شد.")

# ========= قفل‌ها =========
lock_links, lock_stickers, lock_bots, lock_tabcchi = {},{},{},{}
lock_group, lock_voice, lock_music = {},{},{}

@bot.message_handler(func=lambda m: m.text=="قفل ویس")
def lock_voice_cmd(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    lock_voice[m.chat.id]=True
    bot.reply_to(m,"🎙 ویس‌ها قفل شدند.")

@bot.message_handler(func=lambda m: m.text=="باز کردن ویس")
def unlock_voice_cmd(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    lock_voice[m.chat.id]=False
    bot.reply_to(m,"🎙 ویس‌ها آزاد شدند.")

@bot.message_handler(func=lambda m: m.text=="قفل موزیک")
def lock_music_cmd(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    lock_music[m.chat.id]=True
    bot.reply_to(m,"🎵 موزیک‌ها قفل شدند.")

@bot.message_handler(func=lambda m: m.text=="باز کردن موزیک")
def unlock_music_cmd(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    lock_music[m.chat.id]=False
    bot.reply_to(m,"🎵 موزیک‌ها آزاد شدند.")

@bot.message_handler(content_types=['voice'])
def block_voice(m):
    if lock_voice.get(m.chat.id) and not is_admin(m.chat.id, m.from_user.id):
        try: bot.delete_message(m.chat.id, m.message_id)
        except: pass

@bot.message_handler(content_types=['audio'])
def block_music(m):
    if lock_music.get(m.chat.id) and not is_admin(m.chat.id, m.from_user.id):
        try: bot.delete_message(m.chat.id, m.message_id)
        except: pass

# ========= پین پیام =========
@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="پین")
def pin_message(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.pin_chat_message(m.chat.id, m.reply_to_message.message_id)
        bot.reply_to(m,"📌 پیام پین شد.")
    except:
        bot.reply_to(m,"❗ نتوانستم پین کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="حذف پین")
def unpin_message(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.unpin_chat_message(m.chat.id, m.reply_to_message.message_id)
        bot.reply_to(m,"❌ پین حذف شد.")
    except:
        bot.reply_to(m,"❗ نتوانستم حذف پین کنم.")

# ========= پنل مدیریتی در پیوی سودو =========
@bot.message_handler(func=lambda m: m.chat.type=="private" and m.from_user.id==SUDO_ID and m.text=="پنل")
def sudo_panel(m):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📖 راهنما", callback_data="help"))
    kb.add(types.InlineKeyboardButton("📢 ارسال همگانی", callback_data="broadcast"))
    kb.add(types.InlineKeyboardButton("🛠 وضعیت ربات", callback_data="status"))
    bot.send_message(m.chat.id,"🛠 پنل مدیریتی:",reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data=="help")
def cb_help(c): bot.answer_callback_query(c.id); bot.send_message(c.message.chat.id, HELP_TEXT)

@bot.callback_query_handler(func=lambda c: c.data=="status")
def cb_status(c): bot.answer_callback_query(c.id); bot.send_message(c.message.chat.id,"از دستور «وضعیت ربات» داخل گروه استفاده کنید.")

@bot.callback_query_handler(func=lambda c: c.data=="broadcast")
def cb_broadcast(c):
    bot.answer_callback_query(c.id)
    bot.send_message(c.message.chat.id,"📢 متن یا عکس خود را بفرست تا همگانی شود.")
    waiting_broadcast[c.from_user.id] = True

waiting_broadcast = {}
@bot.message_handler(func=lambda m: m.from_user.id==SUDO_ID and waiting_broadcast.get(m.from_user.id))
def do_broadcast(m):
    waiting_broadcast[m.from_user.id] = False
    success = 0
    for gid in list(joined_groups):
        try:
            if m.content_type=="text":
                bot.send_message(gid, m.text)
            elif m.content_type=="photo":
                bot.send_photo(gid, m.photo[-1].file_id, caption=m.caption or "")
            success+=1
        except: pass
    bot.reply_to(m,f"✅ پیام به {success} گروه ارسال شد.")

# ========= RUN =========
print("🤖 Bot is running...")
bot.infinity_polling()
