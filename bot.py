# -*- coding: utf-8 -*-
import os, random, json
from datetime import datetime
import pytz, jdatetime
import telebot
from telebot import types

# ⚙️ تنظیمات اولیه
TOKEN = os.environ.get("BOT_TOKEN") or os.environ.get("BOT_TOK") or "توکن_ربات"
SUDO_ID = int(os.environ.get("SUDO_ID", "123456789"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
sudo_ids = {SUDO_ID}
DATA_FILE = "data.json"

# ========== توابع کمکی ==========
def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f: return json.load(f)
def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump(d, f, ensure_ascii=False, indent=2)
def is_sudo(uid): return uid in sudo_ids
def is_admin(cid, uid):
    try: return bot.get_chat_member(cid, uid).status in ["administrator","creator"]
    except: return False
def cmd_text(m): return (m.text or "").strip()

# ========== 📊 آمار ==========
@bot.message_handler(func=lambda m: cmd_text(m)=="آمار")
def stats(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    try: count = bot.get_chat_member_count(m.chat.id)
    except: count = "نامشخص"
    bot.reply_to(m,f"📊 اعضای گروه: {count}")

# ========== 🧹 پاکسازی ==========
@bot.message_handler(func=lambda m: cmd_text(m)=="پاکسازی")
def clear_chat(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    deleted = 0
    for i in range(1, 201):
        try:
            bot.delete_message(m.chat.id, m.message_id - i)
            deleted += 1
        except: pass
    bot.reply_to(m, f"🧹 {deleted} پیام پاک شد.")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("حذف "))
def delete_x(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    try:
        n = int(cmd_text(m).split()[1])
        deleted = 0
        for i in range(1, n+1):
            bot.delete_message(m.chat.id, m.message_id - i)
            deleted += 1
        bot.reply_to(m, f"🗑 {deleted} پیام پاک شد.")
    except:
        bot.reply_to(m, "❗ فرمت درست: حذف 10")

# ========== 🚫 بن / سکوت / اخطار ==========
banned, muted, warnings = {}, {}, {}
MAX_WARN = 3

def protect(chat_id, uid):
    if is_sudo(uid): return "⚡ کاربر سودو است!"
    try:
        if bot.get_chat_member(chat_id, uid).status == "creator":
            return "❗ این فرد صاحب گروهه."
    except: pass
    return None

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="بن")
def ban_user(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    msg = protect(m.chat.id, uid)
    if msg: return bot.reply_to(m, msg)
    try:
        bot.ban_chat_member(m.chat.id, uid)
        banned.setdefault(m.chat.id,set()).add(uid)
        bot.reply_to(m, "🚫 کاربر بن شد.")
    except: bot.reply_to(m, "❗ خطا در بن")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف بن")
def unban_user(m):
    uid = m.reply_to_message.from_user.id
    try:
        bot.unban_chat_member(m.chat.id, uid)
        banned.get(m.chat.id,set()).discard(uid)
        bot.reply_to(m,"✅ بن حذف شد.")
    except: bot.reply_to(m,"❗ خطا در حذف بن")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="سکوت")
def mute_user(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    msg = protect(m.chat.id, uid)
    if msg: return bot.reply_to(m, msg)
    try:
        bot.restrict_chat_member(m.chat.id, uid, can_send_messages=False)
        muted.setdefault(m.chat.id,set()).add(uid)
        bot.reply_to(m, "🔇 کاربر در سکوت قرار گرفت.")
    except: bot.reply_to(m, "❗ خطا در سکوت")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف سکوت")
def unmute_user(m):
    uid = m.reply_to_message.from_user.id
    try:
        bot.restrict_chat_member(m.chat.id, uid, can_send_messages=True)
        muted.get(m.chat.id,set()).discard(uid)
        bot.reply_to(m,"🔊 سکوت حذف شد.")
    except: bot.reply_to(m,"❗ خطا در حذف سکوت")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="اخطار")
def warn_user(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    warnings.setdefault(m.chat.id, {})
    warnings[m.chat.id][uid] = warnings[m.chat.id].get(uid, 0) + 1
    if warnings[m.chat.id][uid] >= MAX_WARN:
        bot.ban_chat_member(m.chat.id, uid)
        warnings[m.chat.id][uid] = 0
        bot.reply_to(m, "🚫 کاربر با ۳ اخطار بن شد.")
    else:
        bot.reply_to(m, f"⚠️ اخطار {warnings[m.chat.id][uid]}/{MAX_WARN}")

@bot.message_handler(func=lambda m: cmd_text(m)=="لیست اخطار")
def list_warns(m):
    ws = warnings.get(m.chat.id, {})
    if not ws: return bot.reply_to(m,"❗ لیست اخطار خالی است.")
    txt = "\n".join([f"{uid} ➜ {c} اخطار" for uid,c in ws.items()])
    bot.reply_to(m,"⚠️ لیست اخطار:\n"+txt)

# ========== 📌 پن و حذف پن ==========
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="پن")
def pin_msg(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    try:
        bot.pin_chat_message(m.chat.id, m.reply_to_message.message_id)
        bot.reply_to(m,"📌 پیام پین شد.")
    except: bot.reply_to(m,"❗ خطا در پین")

@bot.message_handler(func=lambda m: cmd_text(m)=="حذف پن")
def unpin_all(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    try:
        bot.unpin_all_chat_messages(m.chat.id)
        bot.reply_to(m,"🧹 همه پیام‌های پین حذف شد.")
    except: bot.reply_to(m,"❗ خطا در حذف پن")

# ========== ✉️ ارسال همگانی (فقط سودو) ==========
waiting = {}
@bot.message_handler(func=lambda m: cmd_text(m)=="ارسال همگانی")
def ask_broadcast(m):
    if not is_sudo(m.from_user.id): return
    waiting[m.from_user.id]=True
    bot.reply_to(m,"📝 پیام همگانی را بفرست:")

@bot.message_handler(func=lambda m: m.from_user.id in waiting)
def do_broadcast(m):
    if not is_sudo(m.from_user.id): return
    txt=m.text; waiting.pop(m.from_user.id,None)
    data=load_data(); groups=data.get("groups",{})
    sent=0
    for gid in groups.keys():
        try:
            bot.send_message(int(gid),f"📢 پیام همگانی:\n{txt}")
            sent+=1
        except: pass
    bot.reply_to(m,f"✅ ارسال شد به {sent} گروه")

# ========== 👑 مدیر و سودو ==========
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="افزودن مدیر")
def add_admin(m):
    if not is_sudo(m.from_user.id): return
    data=load_data(); uid=m.reply_to_message.from_user.id
    if uid not in data["admins"]:
        data["admins"].append(uid); save_data(data)
    bot.reply_to(m,"👮 مدیر اضافه شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="افزودن سودو")
def add_sudo(m):
    if not is_sudo(m.from_user.id): return
    data=load_data(); uid=m.reply_to_message.from_user.id
    if uid not in data["sudos"]:
        data["sudos"].append(uid); save_data(data); sudo_ids.add(uid)
    bot.reply_to(m,"⚡ سودو جدید اضافه شد.")

# ========== 🧭 پنل مدیریتی ==========
@bot.message_handler(func=lambda m: cmd_text(m)=="پنل")
def panel(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    kb=types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🎉 خوشامد",callback_data="wlc"),
           types.InlineKeyboardButton("🔐 قفل‌ها",callback_data="locks"))
    kb.add(types.InlineKeyboardButton("📘 راهنما",callback_data="help"),
           types.InlineKeyboardButton("📢 همگانی",callback_data="bc"))
    bot.send_message(m.chat.id,"🧭 پنل مدیریت:",reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data=="help")
def cb_help(c):
    txt=("📘 <b>راهنما کامل:</b>\n"
         "🕓 عمومی: ساعت، آیدی، فال، جوک\n"
         "👮 مدیران: بن، سکوت، اخطار، پاکسازی، قفل گروه\n"
         "👑 سودو: ارسال همگانی، افزودن مدیر/سودو\n"
         "🎉 خوشامد: تنظیم متن، روشن/خاموش\n")
    bot.edit_message_text(txt,c.message.chat.id,c.message.message_id,parse_mode="HTML")

# ========== 🚀 اجرا ==========
print("🤖 مرحله ۲ با موفقیت فعال شد.")
bot.infinity_polling(skip_pending=True, timeout=30)
