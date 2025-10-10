# -*- coding: utf-8 -*-
# Persian Lux Panel V15 – Stable Edition
# Designed for Mohammad 👑

import os
import json
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
    if is_sudo(uid):
        return True
    try:
        st = bot.get_chat_member(chat_id, uid).status
        return st in ("administrator", "creator")
    except:
        return False

print("✅ بخش ۱ (تنظیمات پایه + دیتا + ابزارها) با موفقیت لود شد.")


# ================= 👋 خوشامد حرفه‌ای =================
@bot.message_handler(content_types=["new_chat_members"])
def welcome_new(m):
    data = load_data()
    gid = str(m.chat.id)
    data["welcome"].setdefault(gid, {"enabled": True, "type": "text", "content": None, "file_id": None})
    s = data["welcome"][gid]
    if not s.get("enabled", True):
        return
    user = m.new_chat_members[0]
    name = user.first_name or "دوست جدید"
    group_name = m.chat.title or "گروه"
    text = s.get("content") or f"✨ سلام {name}!\nبه <b>{group_name}</b> خوش اومدی 🌸"
    text = text.replace("{name}", name).replace("{group}", group_name)
    if s.get("type") == "photo" and s.get("file_id"):
        bot.send_photo(m.chat.id, s["file_id"], caption=text)
    else:
        bot.send_message(m.chat.id, text)

print("✅ بخش ۲ (خوشامد حرفه‌ای) با موفقیت لود شد.")


# ================= 🚫 مدیریت کاربران =================
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

# 🚫 بن
@bot.message_handler(func=lambda m: cmd_text(m).startswith("بن"))
def ban_user(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    target = get_target_id(m)
    if not target:
        return bot.reply_to(m, "⚠️ لطفاً روی پیام ریپلای کن یا آیدی بده.")
    if is_sudo(target):
        return bot.reply_to(m, "⚡ نمی‌تونم سودو رو بن کنم.")
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
    bot.reply_to(m, f"🚫 <a href='tg://user?id={target}'>کاربر</a> بن شد.", parse_mode="HTML")

# 🔓 حذف بن
@bot.message_handler(func=lambda m: cmd_text(m).startswith("حذف بن"))
def unban_user(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    target = get_target_id(m)
    if not target:
        return bot.reply_to(m, "⚠️ لطفاً روی پیام ریپلای کن یا آیدی بده.")
    gid = str(m.chat.id)
    ensure_data_keys()
    d = load_data()
    if target in d.get("banned", {}).get(gid, []):
        d["banned"][gid].remove(target)
        save_data(d)
    try:
        bot.unban_chat_member(m.chat.id, target)
    except:
        pass
    bot.reply_to(m, f"✅ <a href='tg://user?id={target}'>کاربر</a> از لیست بن خارج شد.", parse_mode="HTML")

# 🔇 سکوت
@bot.message_handler(func=lambda m: cmd_text(m).startswith("سکوت"))
def mute_user(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    target = get_target_id(m)
    if not target:
        return bot.reply_to(m, "⚠️ ریپلای یا آیدی بده.")
    gid = str(m.chat.id)
    ensure_data_keys()
    d = load_data()
    d["muted"].setdefault(gid, [])
    if target in d["muted"][gid]:
        return bot.reply_to(m, "ℹ️ این کاربر قبلاً ساکت شده.")
    d["muted"][gid].append(target)
    save_data(d)
    try:
        perms = types.ChatPermissions(can_send_messages=False)
        bot.restrict_chat_member(m.chat.id, target, permissions=perms)
    except:
        pass
    bot.reply_to(m, f"🔇 <a href='tg://user?id={target}'>کاربر</a> ساکت شد.", parse_mode="HTML")

# 🔊 حذف سکوت
@bot.message_handler(func=lambda m: cmd_text(m).startswith("حذف سکوت"))
def unmute_user(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    target = get_target_id(m)
    if not target:
        return bot.reply_to(m, "⚠️ ریپلای یا آیدی بده.")
    gid = str(m.chat.id)
    ensure_data_keys()
    d = load_data()
    if target in d["muted"].get(gid, []):
        d["muted"][gid].remove(target)
        save_data(d)
    try:
        perms = types.ChatPermissions(can_send_messages=True)
        bot.restrict_chat_member(m.chat.id, target, permissions=perms)
    except:
        pass
    bot.reply_to(m, f"🔊 سکوت <a href='tg://user?id={target}'>کاربر</a> برداشته شد.", parse_mode="HTML")

# ⚠️ اخطار
@bot.message_handler(func=lambda m: cmd_text(m).startswith("اخطار"))
def warn_user(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    target = get_target_id(m)
    if not target:
        return bot.reply_to(m, "⚠️ ریپلای یا آیدی بده.")
    gid = str(m.chat.id)
    ensure_data_keys()
    d = load_data()
    d["warns"].setdefault(gid, {})
    d["warns"][gid][str(target)] = d["warns"][gid].get(str(target), 0) + 1
    save_data(d)
    count = d["warns"][gid][str(target)]
    msg = f"⚠️ <a href='tg://user?id={target}'>کاربر</a> اخطار شماره {count} گرفت."
    if count >= 3:
        bot.ban_chat_member(m.chat.id, target)
        msg += "\n🚫 چون ۳ اخطار گرفت، از گروه حذف شد."
    bot.reply_to(m, msg, parse_mode="HTML")

# 🧹 حذف اخطار
@bot.message_handler(func=lambda m: cmd_text(m).startswith("حذف اخطار"))
def del_warns(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    target = get_target_id(m)
    if not target:
        return bot.reply_to(m, "⚠️ ریپلای یا آیدی بده.")
    gid = str(m.chat.id)
    ensure_data_keys()
    d = load_data()
    if str(target) in d["warns"].get(gid, {}):
        d["warns"][gid].pop(str(target))
        save_data(d)
    bot.reply_to(m, f"✅ اخطارهای <a href='tg://user?id={target}'>کاربر</a> حذف شد.", parse_mode="HTML")

# 📋 لیست‌ها
@bot.message_handler(func=lambda m: cmd_text(m) == "لیست بن")
def list_ban(m):
    d = load_data()
    gid = str(m.chat.id)
    lst = d.get("banned", {}).get(gid, [])
    if not lst:
        return bot.reply_to(m, "🚫 هیچ کاربری بن نشده.")
    text = "\n".join([f"• <a href='tg://user?id={x}'>کاربر {x}</a>" for x in lst])
    bot.reply_to(m, f"🚫 <b>لیست کاربران بن‌شده:</b>\n{text}", parse_mode="HTML")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست سکوت")
def list_mute(m):
    d = load_data()
    gid = str(m.chat.id)
    lst = d.get("muted", {}).get(gid, [])
    if not lst:
        return bot.reply_to(m, "🔇 هیچ کاربری ساکت نیست.")
    text = "\n".join([f"• <a href='tg://user?id={x}'>کاربر {x}</a>" for x in lst])
    bot.reply_to(m, f"🔇 <b>لیست کاربران ساکت:</b>\n{text}", parse_mode="HTML")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست اخطار")
def list_warn(m):
    d = load_data()
    gid = str(m.chat.id)
    warns = d.get("warns", {}).get(gid, {})
    if not warns:
        return bot.reply_to(m, "⚠️ هیچ اخطاری ثبت نشده.")
    text = "\n".join([f"• <a href='tg://user?id={x}'>کاربر {x}</a> — {warns[x]} اخطار" for x in warns])
    bot.reply_to(m, f"⚠️ <b>لیست اخطارها:</b>\n{text}", parse_mode="HTML")

print("✅ بخش ۳ (بن / سکوت / اخطار / لیست‌ها) با موفقیت لود شد.")


# ================= 🔒 قفل‌ها =================
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

print("✅ بخش ۴ (سیستم قفل‌ها) با موفقیت لود شد.")


# ================= 🚀 اجرای نهایی =================
if __name__ == "__main__":
    print("🤖 Persian Lux Panel V15 در حال اجراست...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=40, skip_pending=True)
        except Exception as e:
            logging.error(f"polling crash: {e}")
            time.sleep(5)
