# -*- coding: utf-8 -*-
import telebot, os, threading, time, random
from datetime import datetime
import pytz
from telebot import types

# ================== تنظیمات ==================
TOKEN   = os.environ.get("BOT_TOKEN")   # توکن ربات
SUDO_ID = int(os.environ.get("SUDO_ID","0"))
SUPPORT_ID = "NOORI_NOOR"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
sudo_ids = {SUDO_ID}

# ========= سودو / ادمین =========
def is_sudo(uid): return uid in sudo_ids
def is_admin(chat_id, user_id):
    if is_sudo(user_id): return True
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator","creator")
    except: return False
def cmd_text(m): return (getattr(m,"text",None) or getattr(m,"caption",None) or "").strip()

# ========= حذف خودکار =========
DELETE_DELAY = 7
def auto_del(chat_id,msg_id,delay=DELETE_DELAY):
    def _():
        time.sleep(delay)
        try: bot.delete_message(chat_id,msg_id)
        except: pass
    threading.Thread(target=_).start()

# ========= جواب رندوم به سودو =========
SUDO_REPLIES = [
    "👑 بله سودو جان، در خدمتم.",
    "🤖 بله ارباب! آماده‌ام.",
    "✨ سودوی عزیز، امر بفرمایید.",
    "🔥 چشم سودو، همین الان!",
    "💎 ربات گوش به فرمان سودوست."
]

@bot.message_handler(func=lambda m: cmd_text(m)=="ربات" and is_sudo(m.from_user.id))
def sudo_reply(m):
    msg = bot.reply_to(m, random.choice(SUDO_REPLIES))
    auto_del(m.chat.id, msg.message_id, delay=7)

# ========= دستورات عمومی =========
@bot.message_handler(func=lambda m: cmd_text(m)=="ساعت")
def time_cmd(m):
    now_utc=datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
    now_teh=datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
    msg=bot.reply_to(m,f"⏰ ساعت UTC: {now_utc}\n⏰ ساعت تهران: {now_teh}")
    auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m)=="ایدی")
def id_cmd(m):
    caption=f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 گروه: <code>{m.chat.id}</code>"
    try:
        photos=bot.get_user_profile_photos(m.from_user.id,limit=1)
        if photos.total_count>0:
            msg=bot.send_photo(m.chat.id,photos.photos[0][-1].file_id,caption=caption)
        else:
            msg=bot.reply_to(m,caption)
    except:
        msg=bot.reply_to(m,caption)
    auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m)=="آمار")
def stats(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try: count=bot.get_chat_member_count(m.chat.id)
    except: count="نامشخص"
    msg=bot.reply_to(m,f"📊 اعضای گروه: {count}")
    auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m)=="لینک")
def group_link(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try:
        link=bot.export_chat_invite_link(m.chat.id)
        msg=bot.reply_to(m,f"📎 لینک گروه:\n{link}")
    except:
        msg=bot.reply_to(m,"❗ نتوانستم لینک بگیرم. (بات باید ادمین با مجوز دعوت باشد)")
    auto_del(m.chat.id,msg.message_id)

# ========= وضعیت ربات =========
@bot.message_handler(func=lambda m: cmd_text(m)=="وضعیت ربات")
def status_cmd(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    now=datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
    msg=bot.reply_to(m,f"🤖 ربات فعال است.\n🕒 زمان: {now}")
    auto_del(m.chat.id,msg.message_id)

# ========= راهنما (با بستن) =========
HELP_TEXT = """
📖 لیست دستورات:

⏰ ساعت | 🆔 ایدی | 📊 آمار | 📎 لینک 
🎉 خوشامد روشن/خاموش | متن/عکس/ریست
🔒 قفل‌ها + پنل
🚫 بن / ✅ حذف بن (ریپلای)
🔕 سکوت / 🔊 حذف سکوت (ریپلای)
⚠️ اخطار / حذف اخطار
👑 مدیر / ❌ حذف مدیر
📌 پن / ❌ حذف پن
🏷 اصل / اصل من / ثبت اصل / حذف اصل
😂 جوک / 🔮 فال (ثبت/لیست/حذف/پاکسازی)
🧹 پاکسازی / حذف [عدد]
📋 لیست مدیران گروه / لیست مدیران ربات
📢 ارسال (سودو) | ➕ افزودن سودو | ➖ حذف سودو
🚪 لفت بده (سودو)
"""

@bot.message_handler(func=lambda m: cmd_text(m)=="راهنما")
def help_cmd(m):
    if m.chat.type!="private" and not is_admin(m.chat.id,m.from_user.id): return
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("❌ بستن", callback_data="close_help"))
    msg=bot.reply_to(m,HELP_TEXT,reply_markup=kb)
    auto_del(m.chat.id,msg.message_id,delay=30)

@bot.callback_query_handler(func=lambda call: call.data=="close_help")
def cb_close_help(call):
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass

# ========= استارت پیوی =========
@bot.message_handler(commands=['start'])
def start_cmd(m):
    if m.chat.type=="private":
        kb=types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("➕ افزودن به گروه", url=f"https://t.me/{bot.get_me().username}?startgroup=new"),
            types.InlineKeyboardButton("📞 پشتیبانی", url=f"https://t.me/{SUPPORT_ID}")
        )
        bot.send_message(m.chat.id,"👋 سلام!\n\nمن ربات مدیریت گروه هستم 🤖",reply_markup=kb)

# ========= اجرای ربات =========
print("🤖 Bot 1999 is running...")
bot.infinity_polling(skip_pending=True, timeout=30)
