# -*- coding: utf-8 -*-
import telebot
from telebot import types
from datetime import datetime
import re

# ==================
TOKEN = "توکن_اینجا"
SUDO_ID = 7089376754  # آیدی عددی سودو
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
🖼 قفل عکس / باز کردن عکس
🎥 قفل ویدیو / باز کردن ویدیو
🎭 قفل گیف / باز کردن گیف
📎 قفل فایل / باز کردن فایل
🎶 قفل موزیک / باز کردن موزیک
🎙 قفل ویس / باز کردن ویس
🔄 قفل فوروارد / باز کردن فوروارد
🚫 بن / ✅ حذف بن (ریپلای)
🔕 سکوت / 🔊 حذف سکوت (ریپلای)
👑 مدیر / ❌ حذف مدیر (ریپلای)
📌 پن / ❌ حذف پن (ریپلای)
📋 لیست مدیران گروه
📋 لیست مدیران ربات
🎉 خوشامد روشن / خاموش
✍️ خوشامد متن [متن دلخواه]
🖼 ثبت عکس (ریپلای روی عکس و بفرست: ثبت عکس)
🧹 پاکسازی (حذف ۵۰ پیام آخر)
⚠️ اخطار (ریپلای)
📢 ارسال (فقط سودو)
🛠 وضعیت ربات
🚪 لفت بده (فقط سودو)
"""

# ========= چک ادمین =========
def is_admin(chat_id, user_id):
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator", "creator") or user_id == SUDO_ID
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

# ========= قفل‌ها =========
locks = {
    "links": {}, "stickers": {}, "bots": {}, "tabchi": {}, "group": {},
    "photo": {}, "video": {}, "gif": {}, "file": {}, "music": {}, "voice": {}, "forward": {}
}

def lock_toggle(chat_id, lock_type, state):
    locks[lock_type][chat_id] = state

@bot.message_handler(func=lambda m: m.text in [
    "قفل لینک","باز کردن لینک","قفل استیکر","باز کردن استیکر",
    "قفل ربات","باز کردن ربات","قفل تبچی","باز کردن تبچی",
    "قفل گروه","باز کردن گروه","قفل عکس","باز کردن عکس",
    "قفل ویدیو","باز کردن ویدیو","قفل گیف","باز کردن گیف",
    "قفل فایل","باز کردن فایل","قفل موزیک","باز کردن موزیک",
    "قفل ویس","باز کردن ویس","قفل فوروارد","باز کردن فوروارد"
])
def toggle_locks(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    t = m.text
    chat_id = m.chat.id
    if t == "قفل لینک": lock_toggle(chat_id,"links",True); bot.reply_to(m,"🔒 لینک قفل شد.")
    elif t == "باز کردن لینک": lock_toggle(chat_id,"links",False); bot.reply_to(m,"🔓 لینک آزاد شد.")
    elif t == "قفل استیکر": lock_toggle(chat_id,"stickers",True); bot.reply_to(m,"🧷 استیکر قفل شد.")
    elif t == "باز کردن استیکر": lock_toggle(chat_id,"stickers",False); bot.reply_to(m,"🧷 استیکر آزاد شد.")
    elif t == "قفل ربات": lock_toggle(chat_id,"bots",True); bot.reply_to(m,"🤖 ربات‌ها قفل شدند.")
    elif t == "باز کردن ربات": lock_toggle(chat_id,"bots",False); bot.reply_to(m,"🤖 ربات‌ها آزاد شدند.")
    elif t == "قفل تبچی": lock_toggle(chat_id,"tabchi",True); bot.reply_to(m,"🚫 تبچی قفل شد.")
    elif t == "باز کردن تبچی": lock_toggle(chat_id,"tabchi",False); bot.reply_to(m,"🚫 تبچی آزاد شد.")
    elif t == "قفل گروه": lock_toggle(chat_id,"group",True); bot.set_chat_permissions(chat_id, types.ChatPermissions(can_send_messages=False)); bot.reply_to(m,"🔐 گروه قفل شد.")
    elif t == "باز کردن گروه": lock_toggle(chat_id,"group",False); bot.set_chat_permissions(chat_id, types.ChatPermissions(can_send_messages=True)); bot.reply_to(m,"✅ گروه باز شد.")
    elif t == "قفل عکس": lock_toggle(chat_id,"photo",True); bot.reply_to(m,"🖼 عکس قفل شد.")
    elif t == "باز کردن عکس": lock_toggle(chat_id,"photo",False); bot.reply_to(m,"🖼 عکس آزاد شد.")
    elif t == "قفل ویدیو": lock_toggle(chat_id,"video",True); bot.reply_to(m,"🎥 ویدیو قفل شد.")
    elif t == "باز کردن ویدیو": lock_toggle(chat_id,"video",False); bot.reply_to(m,"🎥 ویدیو آزاد شد.")
    elif t == "قفل گیف": lock_toggle(chat_id,"gif",True); bot.reply_to(m,"🎭 گیف قفل شد.")
    elif t == "باز کردن گیف": lock_toggle(chat_id,"gif",False); bot.reply_to(m,"🎭 گیف آزاد شد.")
    elif t == "قفل فایل": lock_toggle(chat_id,"file",True); bot.reply_to(m,"📎 فایل قفل شد.")
    elif t == "باز کردن فایل": lock_toggle(chat_id,"file",False); bot.reply_to(m,"📎 فایل آزاد شد.")
    elif t == "قفل موزیک": lock_toggle(chat_id,"music",True); bot.reply_to(m,"🎶 موزیک قفل شد.")
    elif t == "باز کردن موزیک": lock_toggle(chat_id,"music",False); bot.reply_to(m,"🎶 موزیک آزاد شد.")
    elif t == "قفل ویس": lock_toggle(chat_id,"voice",True); bot.reply_to(m,"🎙 ویس قفل شد.")
    elif t == "باز کردن ویس": lock_toggle(chat_id,"voice",False); bot.reply_to(m,"🎙 ویس آزاد شد.")
    elif t == "قفل فوروارد": lock_toggle(chat_id,"forward",True); bot.reply_to(m,"🔄 فوروارد قفل شد.")
    elif t == "باز کردن فوروارد": lock_toggle(chat_id,"forward",False); bot.reply_to(m,"🔄 فوروارد آزاد شد.")

# ========= فیلتر محتوا =========
@bot.message_handler(content_types=['photo','video','document','audio','voice','sticker'])
def block_media(m):
    if locks["photo"].get(m.chat.id) and m.content_type=="photo": bot.delete_message(m.chat.id,m.message_id)
    if locks["video"].get(m.chat.id) and m.content_type=="video": bot.delete_message(m.chat.id,m.message_id)
    if locks["file"].get(m.chat.id) and m.content_type=="document": bot.delete_message(m.chat.id,m.message_id)
    if locks["music"].get(m.chat.id) and m.content_type=="audio": bot.delete_message(m.chat.id,m.message_id)
    if locks["voice"].get(m.chat.id) and m.content_type=="voice": bot.delete_message(m.chat.id,m.message_id)
    if locks["gif"].get(m.chat.id) and (m.document and m.document.mime_type=="video/mp4"): bot.delete_message(m.chat.id,m.message_id)
    if locks["stickers"].get(m.chat.id) and m.content_type=="sticker": bot.delete_message(m.chat.id,m.message_id)

@bot.message_handler(content_types=['text','forward'])
def block_links_forwards(m):
    if locks["links"].get(m.chat.id) and not is_admin(m.chat.id,m.from_user.id):
        if re.search(r"(t\.me|http)", m.text.lower()):
            try: bot.delete_message(m.chat.id,m.message_id)
            except: pass
    if locks["forward"].get(m.chat.id) and m.forward_from:
        try: bot.delete_message(m.chat.id,m.message_id)
        except: pass

# ========= RUN =========
print("🤖 Bot is running...")
bot.infinity_polling()
