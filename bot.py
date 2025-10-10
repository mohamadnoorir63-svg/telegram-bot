# -*- coding: utf-8 -*-
# 🤖 محافظ V1.0 (Funny Mode)
# Designed with ❤️ by Mohammad & ChatGPT

import os
import json
import time
import jdatetime
import telebot
from telebot import types

# ================= ⚙️ تنظیمات پایه =================
TOKEN = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
DATA_FILE = "data.json"


# ================= 💾 فایل داده =================
def base_data():
    return {
        "admins": {},
        "sudo_list": [],
        "banned": {},
        "muted": {},
        "warns": {},
        "filters": {},
        "welcome": {}
    }


def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(base_data())
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


# ================= 🧩 ابزارها =================
def cmd(m):
    return (getattr(m, "text", "") or "").strip()

def is_sudo(uid):
    d = load_data()
    return str(uid) in [str(SUDO_ID)] + d.get("sudo_list", [])

def is_admin(chat_id, uid):
    d = load_data()
    gid = str(chat_id)
    if is_sudo(uid):
        return True
    if str(uid) in d["admins"].get(gid, []):
        return True
    try:
        st = bot.get_chat_member(chat_id, uid).status
        return st in ("administrator", "creator")
    except:
        return False

def time_fa():
    return jdatetime.datetime.now().strftime("%H:%M:%S")

def date_fa():
    return jdatetime.datetime.now().strftime("%A %d %B %Y")

# ================= 👋 خوشامد =================
@bot.message_handler(content_types=["new_chat_members"])
def welcome_new(m):
    d = load_data()
    gid = str(m.chat.id)
    s = d["welcome"].get(gid, {"enabled": True, "msg": None})

    if not s.get("enabled", True):
        return

    for user in m.new_chat_members:
        name = user.first_name or "رفیق جدید"
        msg = s.get("msg") or f"🌸 خوش اومدی {name}!\nخونه خودته 😄"
        bot.send_message(m.chat.id, msg)

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd(m) == "خوشامد روشن")
def enable_welcome(m):
    d = load_data()
    gid = str(m.chat.id)
    d["welcome"].setdefault(gid, {})["enabled"] = True
    save_data(d)
    bot.reply_to(m, "✅ خوشامد فعال شد! از این به بعد با آغوش باز 😄")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd(m) == "خوشامد خاموش")
def disable_welcome(m):
    d = load_data()
    gid = str(m.chat.id)
    d["welcome"].setdefault(gid, {})["enabled"] = False
    save_data(d)
    bot.reply_to(m, "🚫 خوشامد خاموش شد. دیگه خبری از احوال‌پرسی نیست 😅")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd(m) == "تنظیم خوشامد")
def set_welcome(m):
    txt = (m.reply_to_message.text or "").strip()
    if not txt:
        return bot.reply_to(m, "⚠️ لطفاً روی یه پیام متنی ریپلای کن 😁")
    d = load_data()
    gid = str(m.chat.id)
    d["welcome"][gid] = {"enabled": True, "msg": txt}
    save_data(d)
    bot.reply_to(m, "✅ پیام خوشامد با موفقیت تنظیم شد 🌸")


# ================= 🚫 بن / سکوت / اخطار =================
def target_user(m):
    if m.reply_to_message:
        return m.reply_to_message.from_user.id
    parts = cmd(m).split()
    if len(parts) > 1 and parts[1].isdigit():
        return int(parts[1])
    return None

def bot_can(m):
    try:
        me = bot.get_me()
        perms = bot.get_chat_member(m.chat.id, me.id)
        return perms.status in ("administrator", "creator") and getattr(perms, "can_restrict_members", True)
    except:
        bot.reply_to(m, "⚠️ من دسترسی محدودسازی ندارم 😢")
        return False


# 🚫 بن
@bot.message_handler(func=lambda m: cmd(m).startswith("بن "))
def ban_user(m):
    if not is_admin(m.chat.id, m.from_user.id) or not bot_can(m):
        return
    target = target_user(m)
    if not target:
        return bot.reply_to(m, "⚠️ ریپلای کن رو پیام کسی که می‌خوای بن شه 😅")
    if is_admin(m.chat.id, target) or is_sudo(target):
        return bot.reply_to(m, "😎 من با رئیس در نمی‌افتم! اون مدیر یا سودوئه.")

    try:
        bot.ban_chat_member(m.chat.id, target)
        bot.send_message(m.chat.id, f"🚫 کاربر <a href='tg://user?id={target}'>بن شد!</a>\nرفیق، دفعه بعد رعایت کن 😅", parse_mode="HTML")
    except:
        bot.reply_to(m, "⚠️ نتونستم بنش کنم، شاید دسترسی ندارم!")


# 🔇 سکوت
@bot.message_handler(func=lambda m: cmd(m).startswith("سکوت "))
def mute_user(m):
    if not is_admin(m.chat.id, m.from_user.id) or not bot_can(m):
        return
    target = target_user(m)
    if not target:
        return bot.reply_to(m, "⚠️ ریپلای کن رو پیام کسی که می‌خوای ساکت شه 😅")
    if is_admin(m.chat.id, target) or is_sudo(target):
        return bot.reply_to(m, "😂 مدیر یا سودو رو نمی‌تونم ساکت کنم.")

    bot.restrict_chat_member(m.chat.id, target, permissions=types.ChatPermissions(can_send_messages=False))
    bot.send_message(m.chat.id, f"🔇 کاربر <a href='tg://user?id={target}'>ساکت شد!</a>\nبی‌صدا ولی همچنان نازنین 😎", parse_mode="HTML")


# ⚠️ اخطار
@bot.message_handler(func=lambda m: cmd(m).startswith("اخطار "))
def warn_user(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    target = target_user(m)
    if not target:
        return bot.reply_to(m, "⚠️ ریپلای کن رو پیامش 😅")
    if is_admin(m.chat.id, target) or is_sudo(target):
        return bot.reply_to(m, "🤓 به رئیس اخطار نمی‌دن برادر!")

    d = load_data()
    gid = str(m.chat.id)
    d["warns"].setdefault(gid, {})
    d["warns"][gid][str(target)] = d["warns"][gid].get(str(target), 0) + 1
    save_data(d)

    count = d["warns"][gid][str(target)]
    if count >= 3:
        bot.ban_chat_member(m.chat.id, target)
        d["warns"][gid][str(target)] = 0
        save_data(d)
        bot.send_message(m.chat.id, f"🚫 <a href='tg://user?id={target}'>بعد از ۳ اخطار بن شد!</a> 😅", parse_mode="HTML")
    else:
        bot.send_message(m.chat.id, f"⚠️ <a href='tg://user?id={target}'>اخطار شماره {count}</a> گرفت!\nمواظب باش، تا ۳ بشه می‌پرم 😆", parse_mode="HTML")


# ================= 🧾 فیلتر کلمات =================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd(m).startswith("افزودن فیلتر "))
def add_filter(m):
    gid = str(m.chat.id)
    d = load_data()
    word = cmd(m).split(" ", 2)[2].strip().lower()
    d["filters"].setdefault(gid, [])
    if word in d["filters"][gid]:
        return bot.reply_to(m, "😅 این کلمه از قبل فیلتره!")
    d["filters"][gid].append(word)
    save_data(d)
    bot.reply_to(m, f"🚫 کلمه «{word}» فیلتر شد! دیگه کسی حق نداره بگه 😎")

@bot.message_handler(content_types=["text"])
def filter_check(m):
    d = load_data()
    gid = str(m.chat.id)
    filters = d.get("filters", {}).get(gid, [])
    if not filters or is_admin(m.chat.id, m.from_user.id):
        return
    for w in filters:
        if w in m.text.lower():
            bot.delete_message(m.chat.id, m.id)
            msg = bot.send_message(m.chat.id, f"🚫 اون کلمه فیلتره رفیق 😅 رعایت کن!", parse_mode="HTML")
            time.sleep(3)
            bot.delete_message(m.chat.id, msg.id)
            break


# ================= 🚀 اجرا =================
if __name__ == "__main__":
    print("🤖 محافظ V1.0 در حال اجراست...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=40, skip_pending=True)
        except Exception as e:
            print("⚠️ خطا:", e)
            time.sleep(5)
