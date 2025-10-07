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

# ================== کمکی ==================
def is_sudo(uid): return uid in sudo_ids
def is_admin(chat_id, user_id):
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator","creator")
    except: return False

def cmd_text(m): return (getattr(m,"text",None) or "").strip()

# ================== قفل / باز کردن گروه ==================
group_lock = {}

@bot.message_handler(func=lambda m: cmd_text(m)=="قفل گروه")
def lock_group(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    group_lock[m.chat.id] = True
    bot.send_message(m.chat.id, "🔒 گروه به دستور مدیریت بسته شد.\n🚫 کاربران اجازه ارسال پیام ندارند.")

@bot.message_handler(func=lambda m: cmd_text(m)=="باز کردن گروه")
def unlock_group(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    group_lock[m.chat.id] = False
    bot.send_message(m.chat.id, "🔓 گروه باز شد.\n✅ کاربران می‌توانند پیام ارسال کنند.")

# enforce group lock
@bot.message_handler(content_types=['text','photo','video','document','audio','voice','sticker','animation'])
def enforce_group(m):
    if is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id): return
    if group_lock.get(m.chat.id):
        try:
            bot.delete_message(m.chat.id, m.message_id)
        except: pass

# ================== اجرای ربات ==================
print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True, timeout=30)
