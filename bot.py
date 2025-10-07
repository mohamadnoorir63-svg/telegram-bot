# -*- coding: utf-8 -*-
import os, random
from datetime import datetime
import pytz
import telebot

# ================== تنظیمات ==================
TOKEN   = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
sudo_ids = {SUDO_ID}

# ================== کمکی‌ها ==================
def is_sudo(uid): return uid in sudo_ids
def is_admin(chat_id, user_id):
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator", "creator")
    except:
        return False

def cmd_text(m): 
    return (getattr(m,"text",None) or "").strip()

# ================== دستورات عمومی ==================
@bot.message_handler(func=lambda m: cmd_text(m)=="ساعت")
def cmd_time(m):
    now_utc = datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
    now_teh = datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
    bot.reply_to(m, f"⏰ UTC: {now_utc}\n⏰ تهران: {now_teh}")

@bot.message_handler(func=lambda m: cmd_text(m)=="آمار")
def cmd_stats(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try:
        count = bot.get_chat_member_count(m.chat.id)
    except:
        count = "نامشخص"
    bot.reply_to(m, f"📊 اعضای گروه: {count}")

@bot.message_handler(func=lambda m: cmd_text(m)=="ایدی")
def cmd_id(m):
    bot.reply_to(m, f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 گروه: <code>{m.chat.id}</code>")

# ================== جواب سودو «ربات» ==================
SUDO_RESPONSES = ["جونم قربان 😎", "در خدمتم ✌️", "ربات آماده‌ست 🚀", "چه خبر رئیس؟ 🤖"]

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="ربات")
def cmd_sudo(m):
    bot.reply_to(m, random.choice(SUDO_RESPONSES))

# ================== جوک ==================
jokes = []

@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m)=="ثبت جوک")
def joke_add(m):
    if m.reply_to_message and m.reply_to_message.text:
        jokes.append(m.reply_to_message.text)
        bot.reply_to(m, "😂 جوک ذخیره شد")

@bot.message_handler(func=lambda m: cmd_text(m)=="جوک")
def joke_send(m):
    if not jokes:
        return bot.reply_to(m, "❗ جوکی ثبت نشده")
    bot.send_message(m.chat.id, random.choice(jokes))

@bot.message_handler(func=lambda m: cmd_text(m)=="لیست جوک‌ها")
def joke_list(m):
    if not jokes:
        return bot.reply_to(m, "❗ جوکی ثبت نشده")
    txt = "\n".join([f"{i+1}. {j[:40]}" for i,j in enumerate(jokes)])
    bot.reply_to(m, "😂 لیست جوک‌ها:\n" + txt)

@bot.message_handler(func=lambda m: cmd_text(m).startswith("حذف جوک "))
def joke_del(m):
    try:
        idx = int(cmd_text(m).split()[2]) - 1
        if 0 <= idx < len(jokes):
            jokes.pop(idx)
            bot.reply_to(m, "✅ جوک حذف شد")
        else:
            bot.reply_to(m, "❗ شماره نامعتبر")
    except:
        bot.reply_to(m, "❗ فرمت درست: حذف جوک 2")

# ================== فال ==================
fortunes = []

@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m)=="ثبت فال")
def fal_add(m):
    if m.reply_to_message and m.reply_to_message.text:
        fortunes.append(m.reply_to_message.text)
        bot.reply_to(m, "🔮 فال ذخیره شد")

@bot.message_handler(func=lambda m: cmd_text(m)=="فال")
def fal_send(m):
    if not fortunes:
        return bot.reply_to(m, "❗ فالی ثبت نشده")
    bot.send_message(m.chat.id, random.choice(fortunes))

@bot.message_handler(func=lambda m: cmd_text(m)=="لیست فال‌ها")
def fal_list(m):
    if not fortunes:
        return bot.reply_to(m, "❗ فالی ثبت نشده")
    txt = "\n".join([f"{i+1}. {f[:40]}" for i,f in enumerate(fortunes)])
    bot.reply_to(m, "🔮 لیست فال‌ها:\n" + txt)

@bot.message_handler(func=lambda m: cmd_text(m).startswith("حذف فال "))
def fal_del(m):
    try:
        idx = int(cmd_text(m).split()[2]) - 1
        if 0 <= idx < len(fortunes):
            fortunes.pop(idx)
            bot.reply_to(m, "✅ فال حذف شد")
        else:
            bot.reply_to(m, "❗ شماره نامعتبر")
    except:
        bot.reply_to(m, "❗ فرمت درست: حذف فال 2")
print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True, timeout=30)
