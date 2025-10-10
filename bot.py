# -*- coding: utf-8 -*-
# Persian Lux Panel V17 – English Commands + Persian Output
# Designed for Mohammad 👑

import os
import json
import time
import logging
import jdatetime
import telebot
from telebot import types

# ================= ⚙️ BASE CONFIG =================
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

# ================= 💾 DATA SYSTEM =================
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
        "filters": {}
    }

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(base_data())
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
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
    data["locks"].setdefault(gid, {k: False for k in ["link", "group", "photo", "video", "sticker", "gif", "file", "music", "voice", "forward"]})
    save_data(data)

# ================= 🧩 TOOLS =================
def shamsi_date():
    return jdatetime.datetime.now().strftime("%A %d %B %Y")

def shamsi_time():
    return jdatetime.datetime.now().strftime("%H:%M:%S")

def cmd_text(m):
    return (getattr(m, "text", None) or "").strip().lower()

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

print("✅ [1] Base system loaded successfully.")

# ================= 🆔 ID / STATS / TIME / LINK =================

@bot.message_handler(func=lambda m: cmd_text(m) == "id")
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

@bot.message_handler(func=lambda m: cmd_text(m) == "stats")
def show_stats(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)):
        return
    data = load_data()
    users = len(set(data.get("users", [])))
    groups = len(data.get("welcome", {}))
    bot.reply_to(m, f"📊 <b>آمار ربات Persian Lux Panel</b>\n👤 کاربران: {users}\n👥 گروه‌ها: {groups}\n📅 {shamsi_date()} | ⏰ {shamsi_time()}")

@bot.message_handler(func=lambda m: cmd_text(m) == "time")
def show_time(m):
    bot.reply_to(m, f"⏰ {shamsi_time()} | 📅 {shamsi_date()}")

@bot.message_handler(func=lambda m: cmd_text(m) == "botlink")
def bot_link(m):
    bot.reply_to(m, f"🤖 لینک ربات:\nhttps://t.me/{bot.get_me().username}")

@bot.message_handler(func=lambda m: cmd_text(m) == "grouplink")
def group_link(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    try:
        link = bot.export_chat_invite_link(m.chat.id)
        bot.reply_to(m, f"🔗 لینک گروه:\n{link}")
    except:
        bot.reply_to(m, "⚠️ دسترسی ساخت لینک ندارم.")

print("✅ [2] ID, Stats, Time, Link loaded.")

# ================= 👋 WELCOME SYSTEM =================

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
    text = text.replace("{name}", name).replace("{group}", group_name).replace("{time}", shamsi_time()).replace("{date}", shamsi_date())

    if s.get("type") == "photo" and s.get("file_id"):
        bot.send_photo(m.chat.id, s["file_id"], caption=text)
    else:
        bot.send_message(m.chat.id, text)# ================= 🔒 LOCK SYSTEM =================

LOCK_MAP = {
    "link": "link",
    "group": "group",
    "photo": "photo",
    "video": "video",
    "sticker": "sticker",
    "gif": "gif",
    "file": "file",
    "music": "music",
    "voice": "voice",
    "forward": "forward",
    "text": "text"
}

@bot.message_handler(func=lambda m: cmd_text(m).startswith("lock ") or cmd_text(m).startswith("unlock "))
def toggle_lock(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return

    d = load_data()
    gid = str(m.chat.id)
    parts = cmd_text(m).split(" ", 1)
    if len(parts) < 2:
        return bot.reply_to(m, "⚠️ مثال درست:\n<code>lock link</code>")

    key = parts[1]
    lock_type = LOCK_MAP.get(key)
    if not lock_type:
        return bot.reply_to(m, "❌ نوع قفل نامعتبر است.")

    enable = cmd_text(m).startswith("lock ")
    d["locks"].setdefault(gid, {k: False for k in LOCK_MAP.values()})

    if d["locks"][gid][lock_type] == enable:
        return bot.reply_to(m, f"ℹ️ قفل {key} از قبل {'فعال' if enable else 'غیرفعال'} بوده است.")

    d["locks"][gid][lock_type] = enable
    save_data(d)

    if lock_type == "group":
        try:
            perms = types.ChatPermissions(can_send_messages=not enable)
            bot.set_chat_permissions(m.chat.id, perms)
            msg = (
                "🚫 گروه بسته شد ❌\n💬 فقط مدیران می‌توانند پیام دهند."
                if enable
                else "✅ گروه باز شد 🌸\n💬 همه کاربران می‌توانند چت کنند."
            )
            bot.send_message(m.chat.id, msg)
        except Exception as e:
            bot.reply_to(m, f"⚠️ خطا در تغییر وضعیت گروه:\n<code>{e}</code>")
        return

    bot.reply_to(m, f"{'🔒' if enable else '🔓'} قفل <b>{key}</b> {'فعال' if enable else 'غیرفعال'} شد.")

@bot.message_handler(content_types=["text", "photo", "video", "sticker", "animation", "document", "audio", "voice", "forward"])
def lock_filter_system(m):
    d = load_data()
    gid = str(m.chat.id)
    locks = d.get("locks", {}).get(gid, {})
    if not locks:
        return

    def warn_and_delete(reason):
        if is_admin(m.chat.id, m.from_user.id):
            return
        try:
            bot.delete_message(m.chat.id, m.id)
        except:
            pass
        warn = bot.send_message(
            m.chat.id,
            f"🚨 <b>اخطار!</b>\n{reason}\n👤 <a href='tg://user?id={m.from_user.id}'>{m.from_user.first_name}</a> لطفاً قوانین گروه را رعایت کن 🌸",
            parse_mode="HTML",
        )
        time.sleep(3)
        try:
            bot.delete_message(m.chat.id, warn.id)
        except:
            pass

    # 🔗 لینک
    if locks.get("link") and m.text and any(x in m.text.lower() for x in ["http", "www.", "t.me/", "telegram.me/"]):
        return warn_and_delete("ارسال لینک در این گروه مجاز نیست ❌")

    # 💬 متن
    if locks.get("text") and m.text:
        return warn_and_delete("ارسال پیام متنی در این گروه بسته است 💬")

    # 🖼️ عکس
    if locks.get("photo") and m.content_type == "photo":
        return warn_and_delete("ارسال عکس ممنوع است 🖼️")

    # 🎥 ویدیو
    if locks.get("video") and m.content_type == "video":
        return warn_and_delete("ارسال ویدیو مجاز نیست 🎬")

    # 🧸 استیکر
    if locks.get("sticker") and m.content_type == "sticker":
        return warn_and_delete("استفاده از استیکر ممنوع است 🧸")

    # 🎞️ گیف
    if locks.get("gif") and m.content_type == "animation":
        return warn_and_delete("ارسال گیف بسته است 🎞️")

    # 📁 فایل
    if locks.get("file") and m.content_type == "document":
        return warn_and_delete("ارسال فایل مجاز نیست 📁")

    # 🎵 موزیک
    if locks.get("music") and m.content_type == "audio":
        return warn_and_delete("ارسال موزیک ممنوع است 🎵")

    # 🎤 ویس
    if locks.get("voice") and m.content_type == "voice":
        return warn_and_delete("ارسال ویس مجاز نیست 🎤")

    # 🔁 فوروارد
    if locks.get("forward") and (m.forward_from or m.forward_from_chat):
        return warn_and_delete("ارسال پیام فورواردی ممنوع است 🔁")

print("✅ [3] Lock System loaded successfully.")

# ================= 👮 ADMIN & SUDO MANAGEMENT =================

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).startswith("addsudo"))
def add_sudo(m):
    parts = cmd_text(m).split()
    if len(parts) < 2 and not m.reply_to_message:
        return bot.reply_to(m, "⚠️ لطفاً آیدی عددی بده یا روی پیام کاربر ریپلای کن.")
    target = m.reply_to_message.from_user.id if m.reply_to_message else parts[1]
    data = load_data()
    if str(target) not in data["sudo_list"]:
        data["sudo_list"].append(str(target))
        save_data(data)
        bot.reply_to(m, f"👑 کاربر <code>{target}</code> به عنوان سودو اضافه شد.")
    else:
        bot.reply_to(m, "ℹ️ این کاربر از قبل در لیست سودوهاست.")

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).startswith("delsudo"))
def del_sudo(m):
    parts = cmd_text(m).split()
    if len(parts) < 2 and not m.reply_to_message:
        return bot.reply_to(m, "⚠️ لطفاً آیدی بده یا روی پیام فرد ریپلای کن.")
    target = m.reply_to_message.from_user.id if m.reply_to_message else parts[1]
    data = load_data()
    if str(target) in data["sudo_list"]:
        data["sudo_list"].remove(str(target))
        save_data(data)
        bot.reply_to(m, f"🗑️ کاربر <code>{target}</code> از سودو حذف شد.")
    else:
        bot.reply_to(m, "❌ این کاربر سودو نیست.")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("addadmin"))
def add_admin(m):
    gid = str(m.chat.id)
    data = load_data()
    if m.reply_to_message:
        target = m.reply_to_message.from_user.id
    else:
        parts = cmd_text(m).split()
        if len(parts) < 2 or not parts[1].isdigit():
            return bot.reply_to(m, "⚠️ لطفاً روی پیام فرد ریپلای کن یا آیدی عددی بده.")
        target = int(parts[1])
    data["admins"].setdefault(gid, [])
    if str(target) in data["admins"][gid]:
        return bot.reply_to(m, "ℹ️ این کاربر از قبل مدیر بوده.")
    data["admins"][gid].append(str(target))
    save_data(data)
    bot.reply_to(m, f"👮‍♂️ کاربر <code>{target}</code> مدیر گروه شد.")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("deladmin"))
def del_admin(m):
    gid = str(m.chat.id)
    data = load_data()
    if m.reply_to_message:
        target = m.reply_to_message.from_user.id
    else:
        parts = cmd_text(m).split()
        if len(parts) < 2 or not parts[1].isdigit():
            return bot.reply_to(m, "⚠️ لطفاً آیدی بده یا ریپلای کن.")
        target = int(parts[1])
    if str(target) not in data["admins"].get(gid, []):
        return bot.reply_to(m, "❌ این کاربر مدیر نیست.")
    data["admins"][gid].remove(str(target))
    save_data(data)
    bot.reply_to(m, f"🗑️ مدیر <code>{target}</code> حذف شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "adminlist")
def list_admins(m):
    data = load_data()
    gid = str(m.chat.id)
    lst = data.get("admins", {}).get(gid, [])
    if not lst:
        return bot.reply_to(m, "👮‍♂️ هیچ مدیری ثبت نشده.")
    text = "\n".join([f"• {x}" for x in lst])
    bot.reply_to(m, f"👮‍♂️ <b>لیست مدیران:</b>\n{text}", parse_mode="HTML")

@bot.message_handler(func=lambda m: cmd_text(m) == "sudolist")
def list_sudos(m):
    data = load_data()
    lst = data.get("sudo_list", [])
    if not lst:
        return bot.reply_to(m, "👑 هنوز سودویی ثبت نشده.")
    text = "\n".join([f"• {x}" for x in lst])
    bot.reply_to(m, f"👑 <b>لیست سودوها:</b>\n{text}", parse_mode="HTML")

print("✅ [4] Admin & Sudo System loaded successfully.")# ================= 🚫 BAN / MUTE / WARN SYSTEM =================

def bot_can_restrict(m):
    try:
        me = bot.get_me()
        perms = bot.get_chat_member(m.chat.id, me.id)
        if perms.status in ("administrator", "creator") and getattr(perms, "can_restrict_members", True):
            return True
    except:
        pass
    bot.reply_to(m, "⚠️ من ادمین نیستم یا اجازه محدودسازی کاربران رو ندارم.")
    return False

def target_user(m):
    if m.reply_to_message:
        return m.reply_to_message.from_user.id
    parts = cmd_text(m).split()
    if len(parts) > 1 and parts[1].isdigit():
        return int(parts[1])
    return None

# 🚫 BAN USER
@bot.message_handler(func=lambda m: cmd_text(m).startswith("ban"))
def ban_user(m):
    if not is_admin(m.chat.id, m.from_user.id) or not bot_can_restrict(m):
        return
    target = target_user(m)
    if not target:
        return bot.reply_to(m, "⚠️ روی پیام کاربر ریپلای کن یا آیدی بده.")
    if is_admin(m.chat.id, target) or is_sudo(target):
        return bot.reply_to(m, "😎 نمی‌تونی مدیر یا سودو رو بن کنی!")
    d = load_data()
    gid = str(m.chat.id)
    d["banned"].setdefault(gid, [])
    if target in d["banned"][gid]:
        return bot.reply_to(m, "ℹ️ این کاربر قبلاً بن شده.")
    d["banned"][gid].append(target)
    save_data(d)
    try:
        bot.ban_chat_member(m.chat.id, target)
    except:
        return bot.reply_to(m, "⚠️ دسترسی بن کردن ندارم.")
    bot.send_message(m.chat.id, f"🚫 <a href='tg://user?id={target}'>کاربر</a> بن شد ❌", parse_mode="HTML")

# ✅ UNBAN USER
@bot.message_handler(func=lambda m: cmd_text(m).startswith("unban"))
def unban_user(m):
    if not is_admin(m.chat.id, m.from_user.id) or not bot_can_restrict(m):
        return
    target = target_user(m)
    if not target:
        return bot.reply_to(m, "⚠️ ریپلای یا آیدی بده.")
    d = load_data()
    gid = str(m.chat.id)
    if target not in d["banned"].get(gid, []):
        return bot.reply_to(m, "ℹ️ این کاربر بن نیست.")
    d["banned"][gid].remove(target)
    save_data(d)
    bot.unban_chat_member(m.chat.id, target)
    bot.send_message(m.chat.id, "✅ کاربر از بن خارج شد 🌸")

# 🔇 MUTE USER
@bot.message_handler(func=lambda m: cmd_text(m).startswith("mute"))
def mute_user(m):
    if not is_admin(m.chat.id, m.from_user.id) or not bot_can_restrict(m):
        return
    target = target_user(m)
    if not target:
        return bot.reply_to(m, "⚠️ روی پیام کاربر ریپلای کن یا آیدی بده.")
    if is_admin(m.chat.id, target) or is_sudo(target):
        return bot.reply_to(m, "😎 نمی‌تونی مدیر یا سودو رو ساکت کنی!")
    d = load_data()
    gid = str(m.chat.id)
    d["muted"].setdefault(gid, [])
    if target in d["muted"][gid]:
        return bot.reply_to(m, "ℹ️ این کاربر از قبل ساکت بوده.")
    d["muted"][gid].append(target)
    save_data(d)
    bot.restrict_chat_member(m.chat.id, target, permissions=types.ChatPermissions(can_send_messages=False))
    bot.send_message(m.chat.id, f"🔇 کاربر <a href='tg://user?id={target}'>ساکت</a> شد 💬", parse_mode="HTML")

# 🔊 UNMUTE USER
@bot.message_handler(func=lambda m: cmd_text(m).startswith("unmute"))
def unmute_user(m):
    if not is_admin(m.chat.id, m.from_user.id) or not bot_can_restrict(m):
        return
    target = target_user(m)
    if not target:
        return bot.reply_to(m, "⚠️ ریپلای یا آیدی بده.")
    d = load_data()
    gid = str(m.chat.id)
    if target not in d["muted"].get(gid, []):
        return bot.reply_to(m, "ℹ️ این کاربر در سکوت نیست.")
    d["muted"][gid].remove(target)
    save_data(d)
    bot.restrict_chat_member(m.chat.id, target, permissions=types.ChatPermissions(can_send_messages=True))
    bot.send_message(m.chat.id, "🔊 سکوت از کاربر برداشته شد 🌼", parse_mode="HTML")

# ⚠️ WARN SYSTEM
@bot.message_handler(func=lambda m: cmd_text(m).startswith("warn"))
def warn_user(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    target = target_user(m)
    if not target:
        return bot.reply_to(m, "⚠️ ریپلای یا آیدی بده.")
    if is_admin(m.chat.id, target) or is_sudo(target):
        return bot.reply_to(m, "😎 نمی‌تونی به سودو یا مدیر اخطار بدی!")
    d = load_data()
    gid = str(m.chat.id)
    d["warns"].setdefault(gid, {})
    d["warns"][gid][str(target)] = d["warns"][gid].get(str(target), 0) + 1
    save_data(d)
    count = d["warns"][gid][str(target)]
    msg = f"⚠️ کاربر اخطار شماره <b>{count}</b> دریافت کرد."
    if count >= 3:
        try:
            bot.ban_chat_member(m.chat.id, target)
            msg += "\n🚫 به دلیل ۳ اخطار بن شد."
            d["warns"][gid][str(target)] = 0
            save_data(d)
        except:
            msg += "\n⚠️ نتونستم بنش کنم (دسترسی محدود است)."
    bot.send_message(m.chat.id, msg, parse_mode="HTML")

# ================= 🚫 FILTER SYSTEM =================

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("addfilter"))
def add_filter(m):
    gid = str(m.chat.id)
    data = load_data()
    parts = cmd_text(m).split(" ", 1)
    if len(parts) < 2:
        return bot.reply_to(m, "⚠️ مثال:\n<code>addfilter سلام</code>")
    word = parts[1].strip().lower()
    data["filters"].setdefault(gid, [])
    if word in data["filters"][gid]:
        return bot.reply_to(m, "ℹ️ این کلمه از قبل فیلتر شده.")
    data["filters"][gid].append(word)
    save_data(data)
    bot.reply_to(m, f"🚫 کلمه <b>{word}</b> به فیلتر اضافه شد.", parse_mode="HTML")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("delfilter"))
def del_filter(m):
    gid = str(m.chat.id)
    data = load_data()
    parts = cmd_text(m).split(" ", 1)
    if len(parts) < 2:
        return bot.reply_to(m, "⚠️ مثال:\n<code>delfilter سلام</code>")
    word = parts[1].strip().lower()
    if word not in data.get("filters", {}).get(gid, []):
        return bot.reply_to(m, "❌ این کلمه در فیلتر نیست.")
    data["filters"][gid].remove(word)
    save_data(data)
    bot.reply_to(m, f"✅ کلمه <b>{word}</b> از فیلتر حذف شد.", parse_mode="HTML")

@bot.message_handler(func=lambda m: cmd_text(m) == "filterlist")
def list_filters(m):
    gid = str(m.chat.id)
    data = load_data()
    lst = data.get("filters", {}).get(gid, [])
    if not lst:
        return bot.reply_to(m, "🔍 هیچ کلمه‌ای فیلتر نشده.")
    text = "\n".join([f"• {x}" for x in lst])
    bot.reply_to(m, f"🚫 <b>کلمات فیلترشده:</b>\n{text}", parse_mode="HTML")

@bot.message_handler(content_types=["text"])
def filter_check(m):
    data = load_data()
    gid = str(m.chat.id)
    filters = data.get("filters", {}).get(gid, [])
    if not filters or is_admin(m.chat.id, m.from_user.id):
        return
    t = cmd_text(m)
    for word in filters:
        if word in t:
            try:
                bot.delete_message(m.chat.id, m.id)
                warn = bot.send_message(m.chat.id, f"🚫 کلمه <b>{word}</b> در گروه فیلتر است.\n👤 {m.from_user.first_name} رعایت کن 🌸", parse_mode="HTML")
                time.sleep(3)
                bot.delete_message(m.chat.id, warn.id)
  
