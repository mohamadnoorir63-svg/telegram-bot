# -*- coding: utf-8 -*-
import telebot
from telebot import types
from datetime import datetime
import re

# ==================
TOKEN = "7462131830:AAEGzgbjETaf3eukzGHW613i4y61Cs7lzTE"
SUDO_ID = 7089376754
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
📢 ارسال (فقط سودو)
🛠 وضعیت ربات
🚪 لفت بده (فقط سودو)
"""

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

# ========= ارتقا و حذف مدیر =========
@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="مدیر")
def promote_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        me_id = bot.get_me().id
        me = bot.get_chat_member(m.chat.id, me_id)
        if me.status != "administrator" or not getattr(me, "can_promote_members", False):
            return bot.reply_to(m, "❗ ربات مجوز «افزودن مدیر» ندارد. لطفاً در تنظیمات ادمین، گزینه Add Admins را روشن کنید.")

        bot.promote_chat_member(
            m.chat.id, m.reply_to_message.from_user.id,
            can_manage_chat=True,
            can_delete_messages=True,
            can_restrict_members=True,
            can_pin_messages=True,
            can_invite_users=True,
            can_manage_video_chats=True,
            can_promote_members=False
        )
        bot.reply_to(m,"👑 کاربر مدیر شد.")
    except Exception as e:
        bot.reply_to(m,f"❗ خطا: {e}")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="حذف مدیر")
def demote_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        me_id = bot.get_me().id
        me = bot.get_chat_member(m.chat.id, me_id)
        if me.status != "administrator" or not getattr(me, "can_promote_members", False):
            return bot.reply_to(m, "❗ ربات مجوز «حذف مدیر» ندارد.")

        bot.promote_chat_member(
            m.chat.id, m.reply_to_message.from_user.id,
            can_manage_chat=False,
            can_delete_messages=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_invite_users=False,
            can_manage_video_chats=False,
            can_promote_members=False
        )
        bot.reply_to(m,"❌ کاربر از مدیریت حذف شد.")
    except Exception as e:
        bot.reply_to(m,f"❗ خطا: {e}")

# ========= پن و حذف پن =========
@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="پن")
def pin_message(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.pin_chat_message(m.chat.id, m.reply_to_message.message_id)
        bot.reply_to(m,"📌 پیام پین شد.")
    except:
        bot.reply_to(m,"❗ نتوانستم پین کنم.")

@bot.message_handler(func=lambda m: m.text=="حذف پن")
def unpin_message(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.unpin_chat_message(m.chat.id)
        bot.reply_to(m,"❌ پیام از پین خارج شد.")
    except:
        bot.reply_to(m,"❗ نتوانستم حذف پن کنم.")

# ========= لیست مدیران گروه =========
@bot.message_handler(func=lambda m: m.text=="لیست مدیران گروه")
def list_group_admins(m):
    try:
        admins = bot.get_chat_administrators(m.chat.id)
        names = [f"- {a.user.first_name} ({a.user.id})" for a in admins]
        bot.reply_to(m,"📋 لیست مدیران گروه:\n" + "\n".join(names))
    except:
        bot.reply_to(m,"❗ نتوانستم مدیران گروه را بخوانم.")

# ========= لیست مدیران ربات =========
@bot.message_handler(func=lambda m: m.text=="لیست مدیران ربات")
def list_bot_admins(m):
    bot.reply_to(m, f"📋 مدیران ربات:\n- سودو اصلی: {SUDO_ID}")

# ========= RUN =========
print("🤖 Bot is running...")
bot.infinity_polling()
