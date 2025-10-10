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
# توکن و آیدی سودو از تنظیمات هاست (Heroku Config Vars) خوانده می‌شوند
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
        "filters": {}  # 👈 بخش فیلترها هم از همینجا تعریف میشه
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

print("✅ بخش ۱ (تنظیمات پایه + دیتا + ابزارها) با موفقیت لود شد.")# ================= 🆔 آیدی / آمار / ساعت / لینک =================

@bot.message_handler(func=lambda m: cmd_text(m) in ["آیدی", "ایدی"])
def show_id(m):
    """نمایش اطلاعات کاربر"""
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
        bot.reply_to(m, f"🆔 <code>{m.from_user.id}</code>\n⏰ {shamsi_time()}")

# ==== آمار ====
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

# ==== ساعت ====
@bot.message_handler(func=lambda m: cmd_text(m) == "ساعت")
def show_time(m):
    bot.reply_to(m, f"⏰ {shamsi_time()} | 📅 {shamsi_date()}")

# ==== لینک ربات ====
@bot.message_handler(func=lambda m: cmd_text(m) == "لینک ربات")
def bot_link(m):
    bot.reply_to(m, f"🤖 لینک ربات:\nhttps://t.me/{bot.get_me().username}")

# ==== لینک گروه ====
@bot.message_handler(func=lambda m: cmd_text(m) == "لینک گروه")
def group_link(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    try:
        link = bot.export_chat_invite_link(m.chat.id)
        bot.reply_to(m, f"🔗 لینک گروه:\n{link}")
    except:
        bot.reply_to(m, "⚠️ دسترسی ساخت لینک ندارم.")

print("✅ بخش ۲ (آیدی، آمار، ساعت و لینک‌ها) با موفقیت لود شد.")# ================= 👋 سیستم خوشامد حرفه‌ای =================

@bot.message_handler(content_types=["new_chat_members"])
def welcome_new(m):
    """ارسال پیام خوشامد برای اعضای جدید"""
    register_group(m.chat.id)
    data = load_data()
    gid = str(m.chat.id)
    settings = data["welcome"].get(gid, {"enabled": True, "type": "text", "content": None, "file_id": None})

    if not settings.get("enabled", True):
        return  # خوشامد خاموش است

    user = m.new_chat_members[0]
    name = user.first_name or "دوست جدید"
    group_name = m.chat.title or "گروه"
    text = settings.get("content") or f"✨ سلام {name}!\nبه <b>{group_name}</b> خوش اومدی 🌸\n⏰ {shamsi_time()}"

    # جایگزینی تگ‌ها در متن
    text = text.replace("{name}", name).replace("{group}", group_name).replace("{time}", shamsi_time()).replace("{date}", shamsi_date())

    # اگر خوشامد از نوع عکس بود
    if settings.get("type") == "photo" and settings.get("file_id"):
        bot.send_photo(m.chat.id, settings["file_id"], caption=text)
    else:
        bot.send_message(m.chat.id, text)


# ================= ⚙️ تنظیمات خوشامد =================

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "خوشامد روشن")
def enable_welcome(m):
    data = load_data()
    gid = str(m.chat.id)
    data["welcome"].setdefault(gid, {})["enabled"] = True
    save_data(data)
    bot.reply_to(m, "✅ پیام خوشامد برای اعضای جدید فعال شد.")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "خوشامد خاموش")
def disable_welcome(m):
    data = load_data()
    gid = str(m.chat.id)
    data["welcome"].setdefault(gid, {})["enabled"] = False
    save_data(data)
    bot.reply_to(m, "🚫 پیام خوشامد برای اعضای جدید غیرفعال شد.")

# ✏️ تنظیم خوشامد متنی
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "تنظیم خوشامد")
def set_welcome_text(m):
    txt = (m.reply_to_message.text or "").strip()
    if not txt:
        return bot.reply_to(m, "⚠️ لطفاً روی یک پیام متنی ریپلای کن تا به عنوان خوشامد ذخیره شود.")
    data = load_data()
    gid = str(m.chat.id)
    data["welcome"][gid] = {"enabled": True, "type": "text", "content": txt, "file_id": None}
    save_data(data)
    bot.reply_to(m, "✅ پیام خوشامد متنی با موفقیت تنظیم شد.")

# 🖼️ تنظیم خوشامد تصویری
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "تنظیم خوشامد عکس")
def set_welcome_photo(m):
    if not m.reply_to_message.photo:
        return bot.reply_to(m, "⚠️ لطفاً روی یک پیام دارای عکس ریپلای کن.")
    file_id = m.reply_to_message.photo[-1].file_id
    caption = (m.reply_to_message.caption or "✨ خوش اومدی {name} به {group} 🌸").strip()
    data = load_data()
    gid = str(m.chat.id)
    data["welcome"][gid] = {"enabled": True, "type": "photo", "content": caption, "file_id": file_id}
    save_data(data)
    bot.reply_to(m, "🖼️ پیام خوشامد تصویری با موفقیت تنظیم شد.")

# 🔍 مشاهده پیام خوشامد فعلی
@bot.message_handler(func=lambda m: cmd_text(m) == "خوشامد")
def show_current_welcome(m):
    data = load_data()
    gid = str(m.chat.id)
    s = data["welcome"].get(gid, None)
    if not s:
        return bot.reply_to(m, "ℹ️ هنوز هیچ خوشامدی تنظیم نشده.")
    status = "✅ فعال" if s.get("enabled", True) else "🚫 غیرفعال"
    typ = "🖼️ تصویری" if s.get("type") == "photo" else "💬 متنی"
    msg = s.get("content") or "(خالی)"
    bot.reply_to(
        m,
        f"📋 <b>وضعیت خوشامد</b>\n"
        f"وضعیت: {status}\n"
        f"نوع: {typ}\n\n"
        f"📄 متن:\n{msg}"
    )

print("✅ بخش ۳ (خوشامد حرفه‌ای) با موفقیت لود شد.")# ================= 🔒 سیستم قفل‌ها (Lock System Pro) =================

# نوع قفل‌ها
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

# 📌 فعال / غیرفعال کردن قفل‌ها
@bot.message_handler(func=lambda m: cmd_text(m).startswith("قفل ") or cmd_text(m).startswith("بازکردن "))
def toggle_lock(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return

    d = load_data()
    gid = str(m.chat.id)
    parts = cmd_text(m).split(" ", 1)
    if len(parts) < 2:
        return bot.reply_to(m, "⚠️ دستور نادرست است.\nمثال: قفل لینک")

    key_fa = parts[1]
    lock_type = LOCK_MAP.get(key_fa)
    if not lock_type:
        return bot.reply_to(m, "❌ نوع قفل معتبر نیست.")

    enable = cmd_text(m).startswith("قفل ")
    d["locks"].setdefault(gid, {k: False for k in LOCK_MAP.values()})

    if d["locks"][gid][lock_type] == enable:
        return bot.reply_to(m, f"ℹ️ قفل {key_fa} از قبل {'فعال' if enable else 'غیرفعال'} بوده است.")

    d["locks"][gid][lock_type] = enable
    save_data(d)

    # قفل گروه (بستن چت)
    if lock_type == "group":
        try:
            perms = types.ChatPermissions(can_send_messages=not enable)
            bot.set_chat_permissions(m.chat.id, perms)
            msg = (
                "🚫 گروه هم‌اکنون <b>بسته شد</b> ❌\n"
                "💬 ارسال پیام فقط برای مدیران فعال است.\n"
                f"⏰ {shamsi_time()}"
            ) if enable else (
                "✅ گروه <b>باز شد</b> 🌸\n"
                "💬 حالا همه می‌تونن دوباره چت کنن!\n"
                f"⏰ {shamsi_time()}"
            )
            bot.send_message(m.chat.id, msg)
        except Exception as e:
            bot.reply_to(m, f"⚠️ خطا در تغییر وضعیت گروه:\n<code>{e}</code>")
        return

    # پیام زیبای فعال/غیرفعال شدن
    msg = (
        f"🔒 قفل <b>{key_fa}</b> با موفقیت فعال شد.\n"
        f"🚫 از این پس ارسال این نوع پیام ممنوع است."
        if enable
        else f"🔓 قفل <b>{key_fa}</b> غیرفعال شد.\n💬 کاربران می‌توانند دوباره از آن استفاده کنند."
    )
    bot.reply_to(m, msg)


# ================= 🚫 کنترل خودکار پیام‌های ممنوعه =================

@bot.message_handler(content_types=["text", "photo", "video", "sticker", "animation", "document", "audio", "voice", "forward"])
def lock_filter_system(m):
    d = load_data()
    gid = str(m.chat.id)
    locks = d.get("locks", {}).get(gid, {})

    if not locks:
        return  # هیچ قفلی تنظیم نشده

    def warn_and_delete(reason):
        """حذف پیام و اخطار زیبا به کاربر"""
        if is_admin(m.chat.id, m.from_user.id):
            return  # مدیران استثنا هستند
        try:
            bot.delete_message(m.chat.id, m.id)
        except:
            pass

        warn_text = (
            f"🚨 <b>اخطار!</b>\n"
            f"{reason}\n"
            f"👤 <a href='tg://user?id={m.from_user.id}'>{m.from_user.first_name}</a> لطفاً قوانین گروه را رعایت کن 🌸"
        )
        msg = bot.send_message(m.chat.id, warn_text, parse_mode="HTML")
        time.sleep(3)
        try:
            bot.delete_message(m.chat.id, msg.id)
        except:
            pass

    # 🔗 قفل لینک
    if locks.get("link") and m.text and any(x in m.text.lower() for x in ["http", "www.", "t.me/", "telegram.me/"]):
        return warn_and_delete("ارسال لینک در این گروه مجاز نیست ❌")

    # 💬 قفل متن
    if locks.get("text") and m.text:
        return warn_and_delete("ارسال پیام متنی در این گروه بسته است 💬")

    # 🖼️ قفل عکس
    if locks.get("photo") and m.content_type == "photo":
        return warn_and_delete("ارسال عکس در این گروه ممنوع است 🖼️")

    # 🎥 قفل ویدیو
    if locks.get("video") and m.content_type == "video":
        return warn_and_delete("ارسال ویدیو در این گروه مجاز نیست 🎬")

    # 🧸 قفل استیکر
    if locks.get("sticker") and m.content_type == "sticker":
        return warn_and_delete("استفاده از استیکر در این گروه ممنوع است 🧸")

    # 🎞️ قفل گیف
    if locks.get("gif") and m.content_type == "animation":
        return warn_and_delete("ارسال گیف در این گروه بسته است 🎞️")

    # 📁 قفل فایل
    if locks.get("file") and m.content_type == "document":
        return warn_and_delete("ارسال فایل در این گروه مجاز نیست 📁")

    # 🎵 قفل موزیک
    if locks.get("music") and m.content_type == "audio":
        return warn_and_delete("ارسال موزیک در این گروه ممنوع است 🎵")

    # 🎤 قفل ویس
    if locks.get("voice") and m.content_type == "voice":
        return warn_and_delete("ارسال ویس در این گروه مجاز نیست 🎤")

    # 🔁 قفل فوروارد
    if locks.get("forward") and (m.forward_from or m.forward_from_chat):
        return warn_and_delete("ارسال پیام فورواردی در این گروه بسته شده است 🔁")

print("✅ بخش ۴ (سیستم قفل‌ها) با موفقیت لود شد.")
bot.infinity_polling(timeout=60, long_polling_timeout=40)
