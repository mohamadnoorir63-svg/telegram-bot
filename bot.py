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
        return st in ("administrator", "creator") or is_sudo(user_id)
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

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="ثبت جوک")
def joke_add(m):
    if m.reply_to_message:
        if m.reply_to_message.text:
            jokes.append(m.reply_to_message.text)
            bot.reply_to(m, "😂 جوک ذخیره شد")
        elif m.reply_to_message.photo:
            jokes.append("[عکس] " + (m.reply_to_message.caption or ""))
            bot.reply_to(m, "😂 جوک (عکس) ذخیره شد")

@bot.message_handler(func=lambda m: cmd_text(m)=="جوک")
def joke_send(m):
    if not jokes:
        return bot.reply_to(m, "❗ جوکی ثبت نشده")
    bot.send_message(m.chat.id, random.choice(jokes))

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="لیست جوک")
def joke_list(m):
    if not jokes:
        return bot.reply_to(m, "❗ جوکی ثبت نشده")
    txt = "\n".join([f"{i+1}. {j[:40]}" for i,j in enumerate(jokes)])
    bot.reply_to(m, "😂 لیست جوک:\n" + txt)

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).startswith("حذف جوک "))
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

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="ثبت فال")
def fal_add(m):
    if m.reply_to_message:
        if m.reply_to_message.text:
            fortunes.append(m.reply_to_message.text)
            bot.reply_to(m, "🔮 فال ذخیره شد")
        elif m.reply_to_message.photo:
            fortunes.append("[عکس] " + (m.reply_to_message.caption or ""))
            bot.reply_to(m, "🔮 فال (عکس) ذخیره شد")

@bot.message_handler(func=lambda m: cmd_text(m)=="فال")
def fal_send(m):
    if not fortunes:
        return bot.reply_to(m, "❗ فالی ثبت نشده")
    bot.send_message(m.chat.id, random.choice(fortunes))

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="لیست فال")
def fal_list(m):
    if not fortunes:
        return bot.reply_to(m, "❗ فالی ثبت نشده")
    txt = "\n".join([f"{i+1}. {f[:40]}" for i,f in enumerate(fortunes)])
    bot.reply_to(m, "🔮 لیست فال:\n" + txt)

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).startswith("حذف فال "))
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

# ================== بن / سکوت / اخطار ==================
banned = {}
muted = {}
warnings = {}

MAX_WARNINGS = 3

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="بن")
def ban(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    try:
        bot.ban_chat_member(m.chat.id, uid)
        banned.setdefault(m.chat.id, set()).add(uid)
        bot.reply_to(m,"🚫 کاربر بن شد")
    except: bot.reply_to(m,"❗ خطا در بن")

@bot.message_handler(func=lambda m: cmd_text(m)=="لیست بن")
def list_ban(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    ids = banned.get(m.chat.id, set())
    if not ids: return bot.reply_to(m,"❗ لیست خالیه")
    txt="\n".join([str(uid) for uid in ids])
    bot.reply_to(m,"🚫 لیست بن:\n"+txt)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="سکوت")
def mute(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    try:
        bot.restrict_chat_member(m.chat.id, uid, can_send_messages=False)
        muted.setdefault(m.chat.id, set()).add(uid)
        bot.reply_to(m,"🔕 کاربر سکوت شد")
    except: bot.reply_to(m,"❗ خطا در سکوت")

@bot.message_handler(func=lambda m: cmd_text(m)=="لیست سکوت")
def list_mute(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    ids = muted.get(m.chat.id, set())
    if not ids: return bot.reply_to(m,"❗ لیست خالیه")
    txt="\n".join([str(uid) for uid in ids])
    bot.reply_to(m,"🔕 لیست سکوت:\n"+txt)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="اخطار")
def warn(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    warnings.setdefault(m.chat.id, {})
    warnings[m.chat.id][uid] = warnings[m.chat.id].get(uid, 0) + 1
    c = warnings[m.chat.id][uid]
    if c >= MAX_WARNINGS:
        bot.ban_chat_member(m.chat.id, uid)
        warnings[m.chat.id][uid] = 0
        bot.reply_to(m,"🚫 کاربر با ۳ اخطار بن شد")
    else:
        bot.reply_to(m,f"⚠️ اخطار {c}/{MAX_WARNINGS}")

@bot.message_handler(func=lambda m: cmd_text(m)=="لیست اخطار")
def list_warn(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    warns = warnings.get(m.chat.id,{})
    if not warns: return bot.reply_to(m,"❗ لیست خالیه")
    txt="\n".join([f"{uid}: {c}" for uid,c in warns.items()])
    bot.reply_to(m,"⚠️ لیست اخطار:\n"+txt)
print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True, timeout=30)
