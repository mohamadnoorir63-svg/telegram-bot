# -*- coding: utf-8 -*-
import os
import re
import time
import json
import telebot
from telebot import types

# ===== تنظیمات اصلی =====
TOKEN = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

DATA_FILE = "data.json"

# ===== توابع داده =====
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"warns": {}, "admins": {}, "banned": {}}, f)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===== بررسی مدیر =====
def is_admin(chat_id, user_id):
    if user_id == SUDO_ID:
        return True
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except:
        return False

# ===== حذف لینک =====
@bot.message_handler(func=lambda m: True, content_types=["text"])
def check_links(m):
    text = m.text.lower()
    if not text:
        return

    # الگوهای لینک
    pattern = r"(t\.me|telegram\.me|http://|https://|@)"
    if re.search(pattern, text):
        if not is_admin(m.chat.id, m.from_user.id):
            try:
                bot.delete_message(m.chat.id, m.message_id)
                warn_user(m)
            except Exception as e:
                print("خطا در حذف لینک:", e)

# ===== سیستم اخطار =====
def warn_user(m):
    data = load_data()
    user_id = str(m.from_user.id)
    chat_id = str(m.chat.id)
    data["warns"].setdefault(chat_id, {})
    data["warns"][chat_id][user_id] = data["warns"][chat_id].get(user_id, 0) + 1
    warns = data["warns"][chat_id][user_id]
    save_data(data)

    if warns >= 3:
        bot.kick_chat_member(m.chat.id, m.from_user.id)
        bot.send_message(m.chat.id, f"🚫 کاربر [{m.from_user.first_name}](tg://user?id={m.from_user.id}) به دلیل ارسال لینک مسدود شد.")
        data["warns"][chat_id][user_id] = 0
        save_data(data)
    else:
        bot.reply_to(m, f"⚠️ اخطار {warns}/3 برای ارسال لینک صادر شد.")

# ===== دستورات مدیر =====
@bot.message_handler(func=lambda m: m.text == "آمار")
def stats(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    data = load_data()
    members = sum(len(c) for c in data["warns"].values())
    bot.reply_to(m, f"📊 کاربران دارای اخطار: {members}")

@bot.message_handler(func=lambda m: m.text == "پاک اخطارها")
def clear_warns(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    data = load_data()
    chat_id = str(m.chat.id)
    data["warns"][chat_id] = {}
    save_data(data)
    bot.reply_to(m, "✅ تمام اخطارهای این گروه پاک شدند.")

@bot.message_handler(commands=["start"])
def start(m):
    bot.reply_to(m, "👋 ربات ضد لینک پیشرفته فعال است.\nارسال لینک در گروه باعث اخطار یا بن می‌شود.")

print("🤖 Anti-Link Bot started...")
while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        print("خطای polling:", e)
        time.sleep(5)
