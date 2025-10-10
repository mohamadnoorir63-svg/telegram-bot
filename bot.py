# -*- coding: utf-8 -*-
# Persian Lux Panel V17 – Fixed Final Edition (Only Groups)
# Designed for Mohammad 👑

import os
import json
import time
import logging
from datetime import datetime
import telebot
from telebot import types

# ================= ⚙️ تنظیمات پایه =================
try:
    import jdatetime
    def shamsi_date():
        return jdatetime.datetime.now().strftime("%A %d %B %Y")
    def shamsi_time():
        return jdatetime.datetime.now().strftime("%H:%M:%S")
    JALALI_OK = True
except Exception:
    def shamsi_date():
        return datetime.now().strftime("%A %d %B %Y")
    def shamsi_time():
        return datetime.now().strftime("%H:%M:%S")
    JALALI_OK = False

TOKEN = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

DATA_FILE = "data.json"
LOG_FILE = "error.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ================= 💾 دیتا =================
def base_data():
    return {
        "welcome": {},
        "locks": {},
        "admins": {},
        "sudo_list": [],
        "banned": {},
        "muted": {},
        "warns": {},
        "filters": {},
        "users": []
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

def ensure_group_struct(gid):
    d = load_data()
    gid = str(gid)
    if gid not in d["welcome"]:
        d["welcome"][gid] = {"enabled": True, "type": "text", "content": None, "file_id": None}
    if gid not in d["locks"]:
        d["locks"][gid] = {k: False for k in ["link", "group", "photo", "video", "sticker", "gif", "file", "music", "voice", "forward", "text"]}
    if gid not in d["admins"]:
        d["admins"][gid] = []
    if gid not in d["banned"]:
        d["banned"][gid] = []
    if gid not in d["muted"]:
        d["muted"][gid] = []
    if gid not in d["warns"]:
        d["warns"][gid] = {}
    if gid not in d["filters"]:
        d["filters"][gid] = []
    save_data(d)

# ================= ابزارها =================
def cmd_text(m):
    return (getattr(m, "text", None) or "").strip()

def first_word(m):
    t = cmd_text(m)
    return t.split()[0] if t else ""

def in_group(m):
    return getattr(m.chat, "type", "") in ("group", "supergroup")

def is_sudo(uid):
    d = load_data()
    return str(uid) in [str(SUDO_ID)] + d.get("sudo_list", [])

def is_admin(chat_id, uid):
    if is_sudo(uid):
        return True
    try:
        st = bot.get_chat_member(chat_id, uid).status
        if st in ("administrator", "creator"):
            return True
    except:
        pass
    d = load_data()
    return str(uid) in list(map(str, d["admins"].get(str(chat_id), [])))

def bot_admin_perms(chat_id):
    try:
        me = bot.get_me()
        cm = bot.get_chat_member(chat_id, me.id)
        perms = {
            "is_admin": cm.status in ("administrator", "creator"),
            "can_restrict": getattr(cm, "can_restrict_members", True),
            "can_delete": getattr(cm, "can_delete_messages", True),
            "can_invite": getattr(cm, "can_invite_users", True),
            "can_change_info": getattr(cm, "can_change_info", True),
            "can_manage_chat": getattr(cm, "can_manage_chat", True)
        }
        return perms
    except:
        return {"is_admin": False, "can_restrict": False, "can_delete": False}

def get_target_id(m):
    parts = cmd_text(m).split()
    if m.reply_to_message:
        return m.reply_to_message.from_user.id
    elif len(parts) > 1 and parts[1].isdigit():
        return int(parts[1])
    return None

def short_name(u):
    return (u.first_name or "کاربر").strip()

# ================= آیدی / آمار / ساعت =================
@bot.message_handler(func=lambda m: in_group(m) and cmd_text(m) in ["آیدی", "ایدی"])
def show_id(m):
    user = m.from_user
    caption = (
        f"👤 <b>نام:</b> {short_name(user)}\n"
        f"🆔 <b>آیدی عددی:</b> <code>{user.id}</code>\n"
        f"💬 <b>آیدی گروه:</b> <code>{m.chat.id}</code>\n"
        f"📅 {shamsi_date()} | ⏰ {shamsi_time()}"
    )
    bot.reply_to(m, caption)

@bot.message_handler(func=lambda m: in_group(m) and cmd_text(m) == "آمار")
def show_stats(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    d = load_data()
    groups = len(d["welcome"])
    users = len(set(d["users"]))
    bot.reply_to(m, f"📊 <b>آمار</b>\n👥 گروه‌ها: {groups}\n👤 کاربران: {users}")

@bot.message_handler(func=lambda m: in_group(m) and cmd_text(m) == "ساعت")
def show_time(m):
    bot.reply_to(m, f"⏰ {shamsi_time()}")

# ================= خوشامد =================
@bot.message_handler(content_types=["new_chat_members"])
def welcome_new(m):
    if not in_group(m): return
    ensure_group_struct(m.chat.id)
    d = load_data()
    s = d["welcome"][str(m.chat.id)]
    if not s.get("enabled", True): return
    user = m.new_chat_members[0]
    name = user.first_name or "دوست جدید"
    group_name = m.chat.title
    text = s.get("content") or f"🌸 سلام {name}!\nبه جمع ما در <b>{group_name}</b> خوش اومدی 😄"
    if s.get("type") == "photo" and s.get("file_id"):
        bot.send_photo(m.chat.id, s["file_id"], caption=text)
    else:
        bot.send_message(m.chat.id, text)

# ================= قفل‌ها =================
LOCK_MAP = {
    "لینک": "link",
    "عکس": "photo",
    "ویدیو": "video",
    "استیکر": "sticker",
    "گیف": "gif",
    "فایل": "file",
    "موزیک": "music",
    "ویس": "voice",
    "فوروارد": "forward",
    "متن": "text",
    "گروه": "group"
}

@bot.message_handler(func=lambda m: in_group(m) and (cmd_text(m).startswith("قفل ") or cmd_text(m).startswith("بازکردن ")))
def toggle_lock(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    ensure_group_struct(m.chat.id)
    d = load_data()
    gid = str(m.chat.id)
    parts = cmd_text(m).split(" ", 1)
    if len(parts) < 2:
        return bot.reply_to(m, "⚠️ مثال: قفل لینک")
    key_fa = parts[1]
    lock_key = LOCK_MAP.get(key_fa)
    if not lock_key:
        return bot.reply_to(m, "❌ نوع قفل نامعتبر است.")
    enable = cmd_text(m).startswith("قفل ")
    d["locks"][gid][lock_key] = enable
    save_data(d)
    if lock_key == "group":
        perms = types.ChatPermissions(can_send_messages=not enable)
        bot.set_chat_permissions(m.chat.id, perms)
        msg = "🚫 گروه بسته شد." if enable else "✅ گروه باز شد."
        return bot.send_message(m.chat.id, msg)
    msg = f"🔒 قفل {key_fa} فعال شد." if enable else f"🔓 قفل {key_fa} غیرفعال شد."
    bot.reply_to(m, msg)

# ================= بن / سکوت / اخطار =================
def need_restrict_perms(m):
    p = bot_admin_perms(m.chat.id)
    if not p["is_admin"] or not p["can_restrict"]:
        bot.reply_to(m, "⚠️ من ادمین نیستم یا اجازه محدودسازی ندارم.")
        return True
    return False

@bot.message_handler(func=lambda m: in_group(m) and first_word(m) == "بن")
def ban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    if need_restrict_perms(m): return
    target = get_target_id(m)
    if not target: return bot.reply_to(m, "⚠️ ریپلای کن یا آیدی بده.")
    ensure_group_struct(m.chat.id)
    d = load_data()
    gid = str(m.chat.id)
    if target not in d["banned"][gid]:
        d["banned"][gid].append(target)
        save_data(d)
    bot.ban_chat_member(m.chat.id, target)
    bot.reply_to(m, f"🚫 <a href='tg://user?id={target}'>کاربر</a> بن شد.", parse_mode="HTML")

@bot.message_handler(func=lambda m: in_group(m) and cmd_text(m).startswith("حذف بن"))
def unban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    if need_restrict_perms(m): return
    target = get_target_id(m)
    if not target: return bot.reply_to(m, "⚠️ ریپلای کن یا آیدی بده.")
    ensure_group_struct(m.chat.id)
    d = load_data()
    gid = str(m.chat.id)
    if target in d["banned"][gid]:
        d["banned"][gid].remove(target)
        save_data(d)
    bot.unban_chat_member(m.chat.id, target)
    bot.reply_to(m, f"✅ <a href='tg://user?id={target}'>کاربر</a> از بن خارج شد.", parse_mode="HTML")

@bot.message_handler(func=lambda m: in_group(m) and first_word(m) == "سکوت")
def mute_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    if need_restrict_perms(m): return
    target = get_target_id(m)
    if not target: return bot.reply_to(m, "⚠️ ریپلای کن یا آیدی بده.")
    ensure_group_struct(m.chat.id)
    d = load_data()
    gid = str(m.chat.id)
    if target not in d["muted"][gid]:
        d["muted"][gid].append(target)
        save_data(d)
    bot.restrict_chat_member(m.chat.id, target, permissions=types.ChatPermissions(can_send_messages=False))
    bot.reply_to(m, f"🔇 <a href='tg://user?id={target}'>کاربر</a> ساکت شد.", parse_mode="HTML")

@bot.message_handler(func=lambda m: in_group(m) and cmd_text(m).startswith("حذف سکوت"))
def unmute_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    if need_restrict_perms(m): return
    target = get_target_id(m)
    if not target: return bot.reply_to(m, "⚠️ ریپلای کن یا آیدی بده.")
    ensure_group_struct(m.chat.id)
    d = load_data()
    gid = str(m.chat.id)
    if target in d["muted"][gid]:
        d["muted"][gid].remove(target)
        save_data(d)
    bot.restrict_chat_member(m.chat.id, target, permissions=types.ChatPermissions(can_send_messages=True))
    bot.reply_to(m, f"🔊 سکوت <a href='tg://user?id={target}'>کاربر</a> برداشته شد.", parse_mode="HTML")

@bot.message_handler(func=lambda m: in_group(m) and first_word(m) == "اخطار")
def warn_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    target = get_target_id(m)
    if not target: return bot.reply_to(m, "⚠️ ریپلای کن یا آیدی بده.")
    ensure_group_struct(m.chat.id)
    d = load_data()
    gid = str(m.chat.id)
    d["warns"][gid][str(target)] = d["warns"][gid].get(str(target), 0) + 1
    save_data(d)
    c = d["warns"][gid][str(target)]
    msg = f"⚠️ <a href='tg://user?id={target}'>کاربر</a> اخطار شماره {c} گرفت."
    if c >= 3:
        bot.ban_chat_member(m.chat.id, target)
        msg += "\n🚫 به دلیل ۳ اخطار بن شد."
    bot.reply_to(m, msg, parse_mode="HTML")

# ================= لیست‌ها =================
@bot.message_handler(func=lambda m: in_group(m) and cmd_text(m) == "لیست بن")
def list_ban(m):
    d = load_data()
    lst = d["banned"].get(str(m.chat.id), [])
    if not lst: return bot.reply_to(m, "🚫 هیچ کاربری بن نشده.")
    text = "\n".join([f"• <a href='tg://user?id={x}'>کاربر {x}</a>" for x in lst])
    bot.reply_to(m, f"🚫 <b>لیست بن:</b>\n{text}", parse_mode="HTML")

@bot.message_handler(func=lambda m: in_group(m) and cmd_text(m) == "لیست سکوت")
def list_mute(m):
    d = load_data()
    lst = d["muted"].get(str(m.chat.id), [])
    if not lst: return bot.reply_to(m, "🔇 هیچ کاربری ساکت نیست.")
    text = "\n".join([f"• <a href='tg://user?id={x}'>کاربر {x}</a>" for x in lst])
    bot.reply_to(m, f"🔇 <b>لیست سکوت:</b>\n{text}", parse_mode="HTML")

@bot.message_handler(func=lambda m: in_group(m) and cmd_text(m) == "لیست اخطار")
def list_warn(m):
    d = load_data()
    warns = d["warns"].get(str(m.chat.id), {})
    if not warns:
        return bot.reply_to(m, "⚠️ هیچ اخطاری ثبت نشده.")
    lines = []
    for uid, c in warns.items():
        lines.append(f"• <a href='tg://user?id={uid}'>کاربر {uid}</a> — {c} اخطار")
    bot.reply_to(m, "⚠️ <b>لیست اخطار:</b>\n" + "\n".join(lines), parse_mode="HTML")

# ================= اجرای نهایی =================
if __name__ == "__main__":
    print("✅ Persian Lux Panel V17 – Fixed Final در حال اجراست...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=40, skip_pending=True)
        except Exception as e:
            logging.error(f"polling crash: {e}")
            time.sleep(5)
