# -*- coding: utf-8 -*-
# Persian Lux Panel V15 – Full Rewrite (ID + Joke Updated)
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
        "falls": []
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

# ================= 🆔 آیدی لوکس =================
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
    except Exception as e:
        logging.error(f"show_id error: {e}")
        bot.reply_to(m, f"🆔 <code>{m.from_user.id}</code>\n⏰ {shamsi_time()}")

# ================= 🕒 آمار / ساعت =================
@bot.message_handler(func=lambda m: cmd_text(m) == "آمار")
def show_stats(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)):
        return
    data = load_data()
    users = len(set(data.get("users", [])))
    groups = len(data.get("welcome", {}))
    bot.reply_to(
        m,
        f"📊 <b>آمار ربات Persian Lux Panel</b>\n"
        f"👤 کاربران: {users}\n👥 گروه‌ها: {groups}\n"
        f"📅 {shamsi_date()} | ⏰ {shamsi_time()}"
    )

@bot.message_handler(func=lambda m: cmd_text(m) == "ساعت")
def show_time(m):
    bot.reply_to(m, f"⏰ {shamsi_time()} | 📅 {shamsi_date()}")

@bot.message_handler(func=lambda m: cmd_text(m) == "لینک ربات")
def bot_link(m):
    bot.reply_to(m, f"🤖 لینک ربات:\nhttps://t.me/{bot.get_me().username}")

@bot.message_handler(func=lambda m: cmd_text(m) == "لینک گروه")
def group_link(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    try:
        link = bot.export_chat_invite_link(m.chat.id)
        bot.reply_to(m, f"🔗 لینک گروه:\n{link}")
    except:
        bot.reply_to(m, "⚠️ دسترسی ساخت لینک ندارم.")

# ================= 👋 خوشامد =================
@bot.message_handler(content_types=["new_chat_members"])
def welcome_new(m):
    register_group(m.chat.id)
    data = load_data()
    gid = str(m.chat.id)
    s = data["welcome"].get(gid, {"enabled": True})
    if not s.get("enabled", True):
        return
    user = m.new_chat_members[0]
    name = user.first_name or "دوست جدید"
    text = s.get("content") or f"✨ سلام {name}!\nبه گروه <b>{m.chat.title}</b> خوش اومدی 🌸\n⏰ {shamsi_time()}"
    text = text.replace("{name}", name).replace("{time}", shamsi_time())
    if s.get("file_id"):
        bot.send_photo(m.chat.id, s["file_id"], caption=text)
    else:
        bot.send_message(m.chat.id, text)

# ================= ⚙️ مدیریت خوشامد =================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "خاموش خوشامد")
def disable_welcome(m):
    data = load_data()
    gid = str(m.chat.id)
    if gid not in data["welcome"]:
        register_group(gid)
    data["welcome"][gid]["enabled"] = False
    save_data(data)
    bot.reply_to(m, "❌ پیام خوشامد برای این گروه غیرفعال شد.")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "روشن خوشامد")
def enable_welcome(m):
    data = load_data()
    gid = str(m.chat.id)
    if gid not in data["welcome"]:
        register_group(gid)
    data["welcome"][gid]["enabled"] = True
    save_data(data)
    bot.reply_to(m, "✅ پیام خوشامد برای این گروه فعال شد.")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "ثبت خوشامد")
def set_welcome(m):
    data = load_data()
    gid = str(m.chat.id)
    if gid not in data["welcome"]:
        register_group(gid)

    msg = m.reply_to_message
    if msg.text:
        data["welcome"][gid]["content"] = msg.text
        data["welcome"][gid]["file_id"] = None
        data["welcome"][gid]["type"] = "text"
        bot.reply_to(m, "✅ پیام خوشامد متنی جدید ثبت شد.")
    elif msg.photo:
        data["welcome"][gid]["file_id"] = msg.photo[-1].file_id
        data["welcome"][gid]["type"] = "photo"
        data["welcome"][gid]["content"] = msg.caption or ""
        bot.reply_to(m, "🖼️ پیام خوشامد تصویری جدید ثبت شد.")
    else:
        return bot.reply_to(m, "⚠️ لطفاً روی یک پیام متنی یا عکس ریپلای کن.")

    save_data(data)

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "نمایش خوشامد")
def show_welcome(m):
    data = load_data()
    gid = str(m.chat.id)
    if gid not in data["welcome"]:
        register_group(gid)
    s = data["welcome"][gid]
    status = "✅ روشن" if s.get("enabled", True) else "❌ خاموش"
    msg = s.get("content") or "پیش‌فرض سیستم"
    bot.reply_to(m, f"📋 <b>وضعیت خوشامد</b>\nوضعیت: {status}\n\n📝 پیام:\n{msg}")

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
    "فوروارد": "forward"
}

@bot.message_handler(func=lambda m: cmd_text(m).startswith("قفل ") or cmd_text(m).startswith("بازکردن "))
def toggle_lock(m):
    ...
# بقیه کدت بدون تغییر# ================= 😂 جوک‌ها و 🔮 فال =================

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "ثبت جوک")
def add_joke(m):
    d = load_data()
    txt = (m.reply_to_message.text or "").strip()
    if not txt:
        return bot.reply_to(m, "⚠️ لطفاً روی پیام متنی ریپلای کن تا جوک ذخیره شود.")
    if txt in d["jokes"]:
        return bot.reply_to(m, "⚠️ این جوک قبلاً ثبت شده بود.")
    d["jokes"].append(txt)
    save_data(d)
    bot.reply_to(m, f"😂 جوک جدید با موفقیت ثبت شد!\n\n«{txt[:60]}...»")

@bot.message_handler(func=lambda m: cmd_text(m) == "جوک")
def random_joke(m):
    d = load_data()
    jokes = d.get("jokes", [])
    if not jokes:
        return bot.reply_to(m, "😅 هنوز هیچ جوکی ثبت نشده!\nبا دستور «ثبت جوک» اضافه کن.")
    bot.reply_to(m, f"😂 <b>جوک امروز:</b>\n{random.choice(jokes)}")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست جوک")
def list_jokes(m):
    d = load_data()
    jokes = d.get("jokes", [])
    if not jokes:
        return bot.reply_to(m, "📋 هیچ جوکی ثبت نشده.")
    text = "\n".join([f"{i+1}. {j}" for i, j in enumerate(jokes)])
    bot.reply_to(m, f"📜 <b>لیست جوک‌های ثبت‌شده:</b>\n{text}")

# ==== فال ====
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "ثبت فال")
def add_fal(m):
    d = load_data()
    txt = (m.reply_to_message.text or "").strip()
    if not txt:
        return bot.reply_to(m, "⚠️ لطفاً روی پیام متنی ریپلای کن تا فال ذخیره شود.")
    if txt in d["falls"]:
        return bot.reply_to(m, "⚠️ این فال قبلاً ثبت شده بود.")
    d["falls"].append(txt)
    save_data(d)
    bot.reply_to(m, f"🔮 فال جدید ثبت شد!\n\n«{txt[:60]}...»")

@bot.message_handler(func=lambda m: cmd_text(m) == "فال")
def random_fal(m):
    d = load_data()
    f = d.get("falls", [])
    if not f:
        return bot.reply_to(m, "😅 هنوز هیچ فالی ثبت نشده!\nبا دستور «ثبت فال» اضافه کن.")
    bot.reply_to(m, f"🔮 <b>فال امروز:</b>\n{random.choice(f)}")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست فال")
def list_fals(m):
    d = load_data()
    f = d.get("falls", [])
    if not f:
        return bot.reply_to(m, "📜 هیچ فالی ثبت نشده.")
    text = "\n".join([f"{i+1}. {x}" for i, x in enumerate(f)])
    bot.reply_to(m, f"📋 <b>لیست فال‌های ثبت‌شده:</b>\n{text}")


# ================= 🧱 فیلتر کلمات =================

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("فیلتر "))
def add_filter_word(m):
    d = load_data()
    gid = str(m.chat.id)
    word = cmd_text(m).split(" ", 1)[1].strip()
    if not word:
        return bot.reply_to(m, "⚠️ لطفاً بعد از دستور بنویس: فیلتر [کلمه]")
    d.setdefault("filters", {})
    d["filters"].setdefault(gid, [])
    if word in d["filters"][gid]:
        return bot.reply_to(m, "⚠️ این کلمه از قبل فیلتر شده.")
    d["filters"][gid].append(word)
    save_data(d)
    bot.reply_to(m, f"🚫 کلمه «{word}» به لیست فیلتر اضافه شد.")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("حذف فیلتر "))
def remove_filter_word(m):
    d = load_data()
    gid = str(m.chat.id)
    word = cmd_text(m).split(" ", 2)[2].strip()
    if not word:
        return bot.reply_to(m, "⚠️ لطفاً بعد از دستور بنویس: حذف فیلتر [کلمه]")
    if gid not in d.get("filters", {}) or word not in d["filters"][gid]:
        return bot.reply_to(m, "❗ این کلمه در لیست فیلتر نیست.")
    d["filters"][gid].remove(word)
    save_data(d)
    bot.reply_to(m, f"✅ کلمه «{word}» از فیلتر حذف شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست فیلتر")
def list_filters(m):
    d = load_data()
    gid = str(m.chat.id)
    words = d.get("filters", {}).get(gid, [])
    if not words:
        return bot.reply_to(m, "📜 هیچ کلمه‌ای فیلتر نشده.")
    text = "\n".join([f"{i+1}. {w}" for i, w in enumerate(words)])
    bot.reply_to(m, f"🚫 <b>لیست کلمات فیلترشده:</b>\n{text}")

# کنترل پیام‌های فیلترشده
@bot.message_handler(func=lambda m: True, content_types=["text"])
def check_filtered_words(m):
    d = load_data()
    gid = str(m.chat.id)
    filters = d.get("filters", {}).get(gid, [])
    if not filters or not m.text:
        return
    for word in filters:
        if word.lower() in m.text.lower():
            try:
                bot.delete_message(m.chat.id, m.id)
                bot.send_message(m.chat.id, f"🚫 کلمه ممنوعه شناسایی شد:\n«{word}»", disable_notification=True)
            except:
                pass
            break# ================= 🚫 بن / سکوت / اخطار =================
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "بن")
def ban_user(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    uid = m.reply_to_message.from_user.id
    if is_sudo(uid):
        return bot.reply_to(m, "⚡ نمی‌تونم سودو رو بن کنم 😅")
    try:
        bot.ban_chat_member(m.chat.id, uid)
        bot.reply_to(m, "🚫 کاربر بن شد و از گروه خارج گردید.")
    except Exception as e:
        bot.reply_to(m, f"❗ خطا در بن کاربر:\n<code>{e}</code>")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف بن")
def unban_user(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    try:
        bot.unban_chat_member(m.chat.id, m.reply_to_message.from_user.id, only_if_banned=True)
        bot.reply_to(m, "✅ کاربر از لیست بن خارج شد.")
    except:
        bot.reply_to(m, "⚠️ نتونستم بن رو حذف کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "سکوت")
def mute_user(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    uid = str(m.reply_to_message.from_user.id)
    d = load_data()
    d["muted"][uid] = True
    save_data(d)
    bot.reply_to(m, f"🔇 کاربر ساکت شد و دیگه نمی‌تونه پیام بده.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف سکوت")
def unmute_user(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    uid = str(m.reply_to_message.from_user.id)
    d = load_data()
    if uid in d["muted"]:
        d["muted"].pop(uid)
        save_data(d)
    bot.reply_to(m, "🔊 سکوت کاربر برداشته شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "اخطار")
def warn_user(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    uid = str(m.reply_to_message.from_user.id)
    d = load_data()
    d["warns"][uid] = d["warns"].get(uid, 0) + 1
    save_data(d)
    count = d["warns"][uid]
    msg = f"⚠️ کاربر اخطار شماره {count} گرفت."
    if count >= 3:
        bot.ban_chat_member(m.chat.id, int(uid))
        msg += "\n🚫 چون ۳ اخطار گرفت، از گروه اخراج شد."
    bot.reply_to(m, msg)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف اخطار")
def del_warn(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    uid = str(m.reply_to_message.from_user.id)
    d = load_data()
    if uid in d["warns"]:
        d["warns"].pop(uid)
        save_data(d)
    bot.reply_to(m, "✅ تمام اخطارهای کاربر پاک شد.")

# ================= 🧹 پاکسازی پیام‌ها =================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("حذف "))
def del_msgs(m):
    try:
        n = int(cmd_text(m).split()[1])
    except:
        return bot.reply_to(m, "⚠️ فرمت درست دستور: حذف 10")
    count = 0
    for i in range(1, n + 1):
        try:
            bot.delete_message(m.chat.id, m.message_id - i)
            count += 1
        except:
            pass
    bot.send_message(m.chat.id, f"🧹 {count} پیام با موفقیت پاک شد.", disable_notification=True)

# ================= 📢 ارسال همگانی =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and m.reply_to_message and cmd_text(m) == "ارسال")
def broadcast(m):
    d = load_data()
    users = list(set(d.get("users", [])))
    groups = [int(g) for g in d["welcome"].keys()]
    msg = m.reply_to_message
    total = 0
    for uid in users + groups:
        try:
            if msg.text:
                bot.send_message(uid, msg.text)
            elif msg.photo:
                bot.send_photo(uid, msg.photo[-1].file_id, caption=msg.caption or "")
            total += 1
        except:
            continue
    bot.reply_to(m, f"📢 پیام برای {total} کاربر ارسال شد 💌")

# ================= ℹ️ راهنما =================
@bot.message_handler(func=lambda m: cmd_text(m) == "راهنما")
def show_help(m):
    txt = (
        "📘 <b>راهنمای Persian Lux Panel V15</b>\n\n"
        "🆔 آیدی لوکس | ساعت | آمار | لینک ربات/گروه\n"
        "👋 خوشامد | تنظیم | روشن/خاموش\n"
        "🔒 قفل‌ها (لینک | عکس | فیلم | گیف...)\n"
        "🚫 بن | 🔇 سکوت | ⚠️ اخطار (۳=اخراج)\n"
        "😂 جوک‌ها: ثبت جوک | جوک | لیست جوک | حذف جوک N\n"
        "🔮 فال‌ها: ثبت فال | فال\n"
        "🧹 حذف N پیام | 📢 ارسال همگانی (فقط سودو)\n\n"
        "👑 سازنده: محمد | Persian Lux Panel"
    )
    bot.reply_to(m, txt)# ================= 🤖 پاسخ خودکار سودو =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).lower() in ["سلام", "ربات", "هی", "bot"])
def sudo_reply(m):
    replies = [
        f"👑 جانم {m.from_user.first_name} 💎",
        f"✨ سلام {m.from_user.first_name}! آماده‌ام هر دستوری بدی اجرا می‌کنم 💪",
        f"🤖 بله {m.from_user.first_name}، گوش به فرمانتم 🔥",
        f"🌸 در خدمتم {m.from_user.first_name}، فقط بگو چیکار کنم 😍"
    ]
    bot.reply_to(m, random.choice(replies))

# ================= 🚪 خروج از گروه =================
@bot.message_handler(func=lambda m: cmd_text(m) in ["لفت بده", "ترک گروه", "خارج شو"])
def leave_group(m):
    if not is_sudo(m.from_user.id):
        return bot.reply_to(m, "⚠️ فقط سودو می‌تونه منو از گروه خارج کنه 💬")
    try:
        group_name = m.chat.title or "این گروه"
        bot.reply_to(m, f"👋 با اجازه! از {group_name} خارج می‌شم 🌹")
        time.sleep(1.5)
        bot.leave_chat(m.chat.id)
    except Exception as e:
        bot.reply_to(m, f"❗ خطا در خروج از گروه:\n<code>{e}</code>")# ================= 👑 مدیریت مدیران و سودوها =================

# ➕ افزودن مدیر
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "افزودن مدیر")
def add_admin(m):
    if not is_sudo(m.from_user.id):
        return bot.reply_to(m, "⚠️ فقط سودو می‌تونه مدیر جدید اضافه کنه.")
    data = load_data()
    gid = str(m.chat.id)
    uid = str(m.reply_to_message.from_user.id)
    data["admins"].setdefault(gid, [])
    if uid in data["admins"][gid]:
        return bot.reply_to(m, "ℹ️ این کاربر از قبل مدیر گروهه.")
    data["admins"][gid].append(uid)
    save_data(data)
    bot.reply_to(m, f"✅ <a href='tg://user?id={uid}'>کاربر</a> به مدیران این گروه اضافه شد 🌸")

# 🗑 حذف مدیر
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف مدیر")
def del_admin(m):
    if not is_sudo(m.from_user.id):
        return bot.reply_to(m, "⚠️ فقط سودو می‌تونه مدیر حذف کنه.")
    data = load_data()
    gid = str(m.chat.id)
    uid = str(m.reply_to_message.from_user.id)
    if uid not in data["admins"].get(gid, []):
        return bot.reply_to(m, "❗ این کاربر مدیر نیست.")
    data["admins"][gid].remove(uid)
    save_data(data)
    bot.reply_to(m, f"🗑 مدیر <a href='tg://user?id={uid}'>حذف شد</a>.")

# 📋 لیست مدیران
@bot.message_handler(func=lambda m: cmd_text(m) == "لیست مدیران")
def list_admins(m):
    data = load_data()
    gid = str(m.chat.id)
    lst = data["admins"].get(gid, [])
    if not lst:
        return bot.reply_to(m, "📋 هنوز هیچ مدیری ثبت نشده.")
    msg = "👑 <b>لیست مدیران گروه:</b>\n\n" + "\n".join([f"• <a href='tg://user?id={a}'>کاربر {a}</a>" for a in lst])
    bot.reply_to(m, msg)

# 👑 افزودن سودو (فقط سودو اصلی)
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "افزودن سودو")
def add_sudo(m):
    if m.from_user.id != SUDO_ID:
        return bot.reply_to(m, "⚠️ فقط سودو اصلی می‌تونه سودو جدید بسازه.")
    d = load_data()
    uid = str(m.reply_to_message.from_user.id)
    if uid in d["sudo_list"]:
        return bot.reply_to(m, "ℹ️ این کاربر از قبل سودو است.")
    d["sudo_list"].append(uid)
    save_data(d)
    bot.reply_to(m, f"👑 <a href='tg://u
