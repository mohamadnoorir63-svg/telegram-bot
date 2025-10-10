# -*- coding: utf-8 -*-
# Persian Lux Panel V15 – Base Setup
# Designed for Mohammad 👑

import os
import json
import random
import time
import logging
import jdatetime
import telebot
from telebot import types

# ================= ⚙️ تنظیمات پایه =================
TOKEN = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

DATA_FILE = "data.json"
LOG_FILE = "error.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ================= 💾 فایل داده =================
def base_data():
    return {
        "welcome": {},
        "locks": {},
        "admins": {},
        "sudo_list": [],
        "banned": {},
        "muted": {},
        "warns": {},
        "users": [],
        "jokes": [],
        "falls": [],
        "filters": {}
    }

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(base_data())
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = base_data()
    for k in base_data():
        if k not in data:
            data[k] = base_data()[k]
    save_data(data)
    return data

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def register_group(gid):
    data = load_data()
    gid = str(gid)
    data["welcome"].setdefault(gid, {"enabled": True, "type": "text", "content": None, "file_id": None})
    data["locks"].setdefault(
        gid, {k: False for k in ["link", "group", "photo", "video", "sticker", "gif", "file", "music", "voice", "forward"]}
    )
    save_data(data)

# ================= 🧩 ابزارها =================
def shamsi_date():
    return jdatetime.datetime.now().strftime("%A %d %B %Y")

def shamsi_time():
    return jdatetime.datetime.now().strftime("%H:%M:%S")

def cmd_text(m):
    return (getattr(m, "text", None) or "").strip()

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

print("✅ بخش ۱ (تنظیمات پایه + دیتا + ابزارها) با موفقیت لود شد.")


# ================= 🆔 آیدی / آمار / ساعت / لینک =================
@bot.message_handler(func=lambda m: cmd_text(m) in ["آیدی", "ایدی"])
def show_id(m):
    try:
        user = m.from_user
        name = user.first_name or ""
        uid = user.id
        caption = (
            f"🧾 <b>مشخصات کاربر</b>\n"
            f"👤 نام: {name}\n"
            f"🆔 آیدی عددی: <code>{uid}</code>\n"
            f"💬 آیدی گروه: <code>{m.chat.id}</code>\n"
            f"📅 تاریخ: {shamsi_date()}\n"
            f"⏰ ساعت: {shamsi_time()}"
        )
        photos = bot.get_user_profile_photos(uid)
        if photos.total_count > 0:
            file_id = photos.photos[0][-1].file_id
            bot.send_photo(m.chat.id, file_id, caption=caption)
        else:
            bot.reply_to(m, caption)
    except:
        bot.reply_to(m, f"🆔 <code>{m.from_user.id}</code>\n⏰ {shamsi_time()}")

@bot.message_handler(func=lambda m: cmd_text(m) == "آمار")
def show_stats(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)):
        return
    data = load_data()
    users = len(set(data.get("users", [])))
    groups = len(data.get("welcome", {}))
    bot.reply_to(m, f"📊 آمار:\n👤 کاربران: {users}\n👥 گروه‌ها: {groups}")

@bot.message_handler(func=lambda m: cmd_text(m) == "ساعت")
def show_time(m):
    bot.reply_to(m, f"⏰ {shamsi_time()} | 📅 {shamsi_date()}")

print("✅ بخش ۲ (آیدی، آمار، ساعت و لینک‌ها) با موفقیت لود شد.")


# ================= 👋 خوشامد حرفه‌ای =================
@bot.message_handler(content_types=["new_chat_members"])
def welcome_new(m):
    register_group(m.chat.id)
    data = load_data()
    gid = str(m.chat.id)
    s = data["welcome"].get(gid, {"enabled": True, "type": "text", "content": None, "file_id": None})
    if not s.get("enabled", True):
        return
    user = m.new_chat_members[0]
    name = user.first_name or "دوست جدید"
    group_name = m.chat.title or "گروه"
    text = s.get("content") or f"✨ سلام {name}!\nبه <b>{group_name}</b> خوش اومدی 🌸\n⏰ {shamsi_time()}"
    if s.get("type") == "photo" and s.get("file_id"):
        bot.send_photo(m.chat.id, s["file_id"], caption=text)
    else:
        bot.send_message(m.chat.id, text)

print("✅ بخش ۳ (خوشامد حرفه‌ای) با موفقیت لود شد.")


# ================= 🚫 مدیریت کاربران (بن / سکوت / اخطار) =================
def ensure_data_keys():
    d = load_data()
    for key in ["banned", "muted", "warns"]:
        if key not in d:
            d[key] = {}
    save_data(d)

def get_target_id(m):
    parts = cmd_text(m).split()
    if m.reply_to_message:
        return m.reply_to_message.from_user.id
    elif len(parts) > 1 and parts[1].isdigit():
        return int(parts[1])
    return None

@bot.message_handler(func=lambda m: cmd_text(m).startswith("بن"))
def ban_user(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    target = get_target_id(m)
    if not target:
        return bot.reply_to(m, "⚠️ لطفاً ریپلای کن یا آیدی بده.")
    gid = str(m.chat.id)
    ensure_data_keys()
    d = load_data()
    d["banned"].setdefault(gid, [])
    if target not in d["banned"][gid]:
        d["banned"][gid].append(target)
        save_data(d)
    try:
        bot.ban_chat_member(m.chat.id, target)
    except:
        pass
    bot.reply_to(m, f"🚫 کاربر <a href='tg://user?id={target}'>بن شد</a>.", parse_mode="HTML")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("اخطار"))
def warn_user(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    target = get_target_id(m)
    if not target:
        return bot.reply_to(m, "⚠️ روی پیام ریپلای کن یا آیدی بده.")
    gid = str(m.chat.id)
    ensure_data_keys()
    d = load_data()
    d["warns"].setdefault(gid, {})
    d["warns"][gid][str(target)] = d["warns"][gid].get(str(target), 0) + 1
    save_data(d)
    c = d["warns"][gid][str(target)]
    msg = f"⚠️ <a href='tg://user?id={target}'>کاربر</a> اخطار شماره {c} گرفت."
    if c >= 3:
        bot.ban_chat_member(m.chat.id, target)
        msg += "\n🚫 چون ۳ اخطار گرفت، از گروه حذف شد."
    bot.reply_to(m, msg, parse_mode="HTML")

print("✅ بخش ۴ (بن / سکوت / اخطار) با موفقیت لود شد.")


# ================= 🔒 سیستم قفل‌ها (Lock System Pro) =================
LOCK_MAP = {
    "لینک": "link",
    "گروه": "group",
    "عکس": "photo",
    "ویدیو": "video",
    "استیکر": "sticker",
    "گیف": "gif",
    "فایل": "file",
    "موزیک": "music",
    "ویس": "voice",
    "فوروارد": "forward",
    "متن": "text"
}

@bot.message_handler(func=lambda m: cmd_text(m).startswith("قفل ") or cmd_text(m).startswith("بازکردن "))
def toggle_lock(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    d = load_data()
    gid = str(m.chat.id)
    parts = cmd_text(m).split(" ", 1)
    if len(parts) < 2:
        return bot.reply_to(m, "⚠️ مثال: قفل لینک")
    key_fa = parts[1]
    lock_type = LOCK_MAP.get(key_fa)
    if not lock_type:
        return bot.reply_to(m, "❌ نوع قفل معتبر نیست.")
    enable = cmd_text(m).startswith("قفل ")
    d["locks"].setdefault(gid, {k: False for k in LOCK_MAP.values()})
    d["locks"][gid][lock_type] = enable
    save_data(d)
    msg = "🔒 قفل فعال شد" if enable else "🔓 قفل غیرفعال شد"
    bot.reply_to(m, msg)

print("✅ بخش ۵ (قفل‌ها) با موفقیت لود شد.")


# ================= 🚀 اجرای نهایی =================
if __name__ == "__main__":
    print("🤖 Persian Lux Panel V15 در حال اجراست...")
    while True:
        try:
            bot.infinity_polling(
                timeout=60,
                long_polling_timeout=40,
                skip_pending=True
            )
        except Exception as e:
            logging.error(f"polling crash: {e}")
            time.sleep(5)
