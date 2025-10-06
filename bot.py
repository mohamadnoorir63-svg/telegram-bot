# -*- coding: utf-8 -*-
import os, time, threading, random
from datetime import datetime
import pytz
import telebot
from telebot import types

# ================== تنظیمات ==================
TOKEN     = os.environ.get("BOT_TOKEN")
SUDO_ID   = int(os.environ.get("SUDO_ID", "0"))
SUPPORT_ID = "NOORI_NOOR"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
sudo_ids = {SUDO_ID}

# ================== کمکی‌ها ==================
def is_sudo(uid): return uid in sudo_ids
def is_admin(chat_id, user_id):
    if is_sudo(user_id): return True
    try: st = bot.get_chat_member(chat_id, user_id).status
    except: return False
    return st in ("administrator","creator")

def cmd_text(m): return (getattr(m,"text",None) or getattr(m,"caption",None) or "").strip()

DELETE_DELAY = 7
def auto_del(chat_id, msg_id, delay=DELETE_DELAY):
    def _():
        time.sleep(delay)
        try: bot.delete_message(chat_id,msg_id)
        except: pass
    threading.Thread(target=_, daemon=True).start()

# ================== دستورات عمومی ==================
@bot.message_handler(func=lambda m: cmd_text(m)=="ساعت")
def cmd_time(m):
    now_utc=datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
    now_teh=datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
    msg=bot.reply_to(m,f"⏰ UTC: {now_utc}\n⏰ تهران: {now_teh}")
    auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m)=="ایدی")
def cmd_id(m):
    caption=f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 گروه: <code>{m.chat.id}</code>"
    try:
        photos=bot.get_user_profile_photos(m.from_user.id,limit=1)
        if photos.total_count>0:
            msg=bot.send_photo(m.chat.id,photos.photos[0][-1].file_id,caption=caption)
        else: msg=bot.reply_to(m,caption)
    except: msg=bot.reply_to(m,caption)
    auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m)=="آمار")
def cmd_stats(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try: count=bot.get_chat_member_count(m.chat.id)
    except: count="نامشخص"
    msg=bot.reply_to(m,f"📊 اعضای گروه: {count}")
    auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m)=="لینک")
def cmd_link(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try: link=bot.export_chat_invite_link(m.chat.id)
    except: link="❗ خطا در گرفتن لینک."
    msg=bot.reply_to(m,f"📎 {link}")
    auto_del(m.chat.id,msg.message_id)

# ================== راهنما با پل شیشه‌ای ==================
HELP_TEXT = """
📖 لیست دستورات:

⏰ ساعت | 🆔 ایدی 
📊 آمار | 📎 لینک 
🛠 وضعیت ربات
🎉 خوشامد روشن / خاموش
✍️ خوشامد متن [متن]
🖼 ثبت عکس (ریپلای)
🔒 قفل‌ها (پنل)
🚫 بن | ✅ حذف بن (ریپلای)
🔕 سکوت | 🔊 حذف سکوت (ریپلای)
⚠️ اخطار | حذف اخطار (ریپلای)
👑 مدیر | ❌ حذف مدیر (ریپلای)
📌 پن | ❌ حذف پن (ریپلای)
📋 لیست مدیران
🧹 پاکسازی
📢 ارسال (فقط سودو)
➕ افزودن/➖ حذف سودو
🚪 لفت بده (سودو)
🏷 اصل | اصل من
😂 جوک | 🔮 فال
"""

@bot.message_handler(func=lambda m: cmd_text(m)=="راهنما")
def help_cmd(m):
    if m.chat.type!="private" and not is_admin(m.chat.id,m.from_user.id): return
    kb=types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("❌ بستن",callback_data="close_help"))
    msg=bot.reply_to(m,HELP_TEXT,reply_markup=kb)
    auto_del(m.chat.id,msg.message_id,delay=20)

@bot.callback_query_handler(func=lambda c: c.data=="close_help")
def cb_close_help(c):
    try: bot.delete_message(c.message.chat.id,c.message.message_id)
    except: pass
    bot.answer_callback_query(c.id,"❌ بسته شد")

# ================== وضعیت ربات ==================
@bot.message_handler(func=lambda m: cmd_text(m)=="وضعیت ربات")
def cmd_status(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    now=datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
    msg=bot.reply_to(m,f"🤖 فعال هستم\n🕒 {now}")
    auto_del(m.chat.id,msg.message_id)

# جواب سودو «ربات»
SUDO_RESPONSES=["جونم قربان 😎","در خدمتم ✌️","ربات آماده‌ست 🚀","چه خبر رئیس؟ 🤖"]
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="ربات")
def cmd_sudo(m):
    msg=bot.reply_to(m,random.choice(SUDO_RESPONSES))
    auto_del(m.chat.id,msg.message_id)
# ================== اجرا ==================
print("🤖 Bot v1997 is running...")
bot.infinity_polling(skip_pending=True,timeout=30)
