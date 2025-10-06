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

sudo_ids   = {SUDO_ID}
bot_admins = set()

# ================== کمکی‌ها ==================
def is_sudo(uid): return uid in sudo_ids
def is_bot_admin(uid): return uid in bot_admins or is_sudo(uid)
def is_admin(chat_id, user_id):
    if is_bot_admin(user_id): return True
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

# ================== خوشامد ==================
welcome_enabled, welcome_texts, welcome_photos = {}, {}, {}
DEFAULT_WELCOME="• سلام {name} به گروه {title} خوش آمدی 🌹\n📆 {date}\n⏰ {time}"

@bot.message_handler(content_types=['new_chat_members'])
def welcome(m):
    for u in m.new_chat_members:
        if not welcome_enabled.get(m.chat.id): continue
        txt=(welcome_texts.get(m.chat.id,DEFAULT_WELCOME)).format(
            name=u.first_name,title=m.chat.title,
            date=datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y/%m/%d"),
            time=datetime.now(pytz.timezone("Asia/Tehran")).strftime("%H:%M:%S")
        )
        if m.chat.id in welcome_photos:
            bot.send_photo(m.chat.id,welcome_photos[m.chat.id],caption=txt)
        else: bot.send_message(m.chat.id,txt)

@bot.message_handler(func=lambda m: cmd_text(m)=="خوشامد روشن")
def w_on(m): 
    if is_admin(m.chat.id,m.from_user.id):
        welcome_enabled[m.chat.id]=True
        bot.reply_to(m,"✅ خوشامد روشن شد")

@bot.message_handler(func=lambda m: cmd_text(m)=="خوشامد خاموش")
def w_off(m): 
    if is_admin(m.chat.id,m.from_user.id):
        welcome_enabled[m.chat.id]=False
        bot.reply_to(m,"❌ خوشامد خاموش شد")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("خوشامد متن "))
def w_txt(m):
    if is_admin(m.chat.id,m.from_user.id):
        welcome_texts[m.chat.id]=cmd_text(m).replace("خوشامد متن ","",1)
        bot.reply_to(m,"✍️ متن خوشامد ذخیره شد")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="ثبت عکس")
def w_pic(m):
    if is_admin(m.chat.id,m.from_user.id) and m.reply_to_message.photo:
        welcome_photos[m.chat.id]=m.reply_to_message.photo[-1].file_id
        bot.reply_to(m,"🖼 عکس خوشامد ذخیره شد")

# ================== راهنما ==================
HELP_TEXT="""
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
🧹 پاکسازی | حذف [عدد]
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
    bot.send_message(m.chat.id,HELP_TEXT,reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data=="close_help")
def cb_close_help(c):
    try: bot.delete_message(c.message.chat.id,c.message.message_id)
    except: pass
    bot.answer_callback_query(c.id,"❌ بسته شد")
# ================== اجرا ==================
print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True,timeout=30)
