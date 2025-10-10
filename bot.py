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

print("✅ بخش ۴ (سیستم قفل‌ها) با موفقیت لود شد.")# ================= 🧑‍💼 مدیریت مدیران و سودوها =================

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).startswith("افزودن سودو"))
def add_sudo(m):
    parts = cmd_text(m).split()
    if len(parts) < 2 and not m.reply_to_message:
        return bot.reply_to(m, "⚠️ لطفاً آیدی عددی بده یا روی پیام فرد ریپلای کن.")
    target = m.reply_to_message.from_user.id if m.reply_to_message else parts[1]
    data = load_data()
    if str(target) not in data["sudo_list"]:
        data["sudo_list"].append(str(target))
        save_data(data)
        bot.reply_to(m, f"👑 کاربر <code>{target}</code> به عنوان سودو اضافه شد.")
    else:
        bot.reply_to(m, "ℹ️ این کاربر از قبل در لیست سودوها هست.")

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).startswith("حذف سودو"))
def del_sudo(m):
    parts = cmd_text(m).split()
    if len(parts) < 2 and not m.reply_to_message:
        return bot.reply_to(m, "⚠️ لطفاً آیدی بده یا روی پیام فرد ریپلای کن.")
    target = m.reply_to_message.from_user.id if m.reply_to_message else parts[1]
    data = load_data()
    if str(target) in data["sudo_list"]:
        data["sudo_list"].remove(str(target))
        save_data(data)
        bot.reply_to(m, f"🗑️ کاربر <code>{target}</code> از لیست سودوها حذف شد.")
    else:
        bot.reply_to(m, "❌ این کاربر در لیست سودوها نیست.")


@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("افزودن مدیر"))
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
    bot.reply_to(m, f"👮‍♂️ کاربر <code>{target}</code> به عنوان مدیر گروه ثبت شد.")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("حذف مدیر"))
def del_admin(m):
    gid = str(m.chat.id)
    data = load_data()
    if m.reply_to_message:
        target = m.reply_to_message.from_user.id
    else:
        parts = cmd_text(m).split()
        if len(parts) < 2 or not parts[1].isdigit():
            return bot.reply_to(m, "⚠️ لطفاً روی پیام فرد ریپلای کن یا آیدی بده.")
        target = int(parts[1])
    if str(target) not in data["admins"].get(gid, []):
        return bot.reply_to(m, "❌ این کاربر مدیر نیست.")
    data["admins"][gid].remove(str(target))
    save_data(data)
    bot.reply_to(m, f"🗑️ مدیر <code>{target}</code> از گروه حذف شد.")


# ================= 🧾 لیست مدیران و سودوها =================

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست سودو")
def list_sudo(m):
    data = load_data()
    lst = data.get("sudo_list", [])
    if not lst:
        return bot.reply_to(m, "👑 هنوز هیچ سودویی ثبت نشده.")
    text = "\n".join([f"• <a href='tg://user?id={x}'>سودو {x}</a>" for x in lst])
    bot.reply_to(m, f"👑 <b>لیست سودوها:</b>\n{text}", parse_mode="HTML")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست مدیر")
def list_admin(m):
    data = load_data()
    gid = str(m.chat.id)
    lst = data.get("admins", {}).get(gid, [])
    if not lst:
        return bot.reply_to(m, "👮‍♂️ هیچ مدیری ثبت نشده.")
    text = "\n".join([f"• <a href='tg://user?id={x}'>مدیر {x}</a>" for x in lst])
    bot.reply_to(m, f"👮‍♂️ <b>لیست مدیران:</b>\n{text}", parse_mode="HTML")


# ================= 🚫 سیستم فیلتر کلمات =================

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("افزودن فیلتر"))
def add_filter(m):
    gid = str(m.chat.id)
    data = load_data()
    parts = cmd_text(m).split(" ", 1)
    if len(parts) < 2:
        return bot.reply_to(m, "⚠️ لطفاً کلمه‌ای بنویس که می‌خوای فیلتر بشه.\nمثلاً: افزودن فیلتر سلام")
    word = parts[1].strip().lower()
    data["filters"].setdefault(gid, [])
    if word in data["filters"][gid]:
        return bot.reply_to(m, "ℹ️ این کلمه قبلاً فیلتر شده.")
    data["filters"][gid].append(word)
    save_data(data)
    bot.reply_to(m, f"🚫 کلمه <b>{word}</b> به لیست فیلترها اضافه شد.", parse_mode="HTML")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("حذف فیلتر"))
def del_filter(m):
    gid = str(m.chat.id)
    data = load_data()
    parts = cmd_text(m).split(" ", 1)
    if len(parts) < 2:
        return bot.reply_to(m, "⚠️ لطفاً کلمه‌ای بنویس که می‌خوای از فیلتر حذف بشه.")
    word = parts[1].strip().lower()
    if word not in data.get("filters", {}).get(gid, []):
        return bot.reply_to(m, "❌ این کلمه در فیلتر نیست.")
    data["filters"][gid].remove(word)
    save_data(data)
    bot.reply_to(m, f"✅ کلمه <b>{word}</b> از فیلترها حذف شد.", parse_mode="HTML")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست فیلتر")
def list_filters(m):
    gid = str(m.chat.id)
    data = load_data()
    lst = data.get("filters", {}).get(gid, [])
    if not lst:
        return bot.reply_to(m, "🔍 هیچ کلمه‌ای فیلتر نشده.")
    text = "\n".join([f"• {x}" for x in lst])
    bot.reply_to(m, f"🚫 <b>کلمات فیلترشده:</b>\n{text}", parse_mode="HTML")

# حذف خودکار پیام‌های شامل کلمات فیلترشده
@bot.message_handler(content_types=["text"])
def filter_check(m):
    data = load_data()
    gid = str(m.chat.id)
    filters = data.get("filters", {}).get(gid, [])
    if not filters or is_admin(m.chat.id, m.from_user.id):
        return
    t = cmd_text(m).lower()
    for word in filters:
        if word in t:
            try:
                bot.delete_message(m.chat.id, m.id)
                warn = bot.send_message(
                    m.chat.id,
                    f"🚫 <b>{word}</b> در گروه فیلتر است.\n👤 <a href='tg://user?id={m.from_user.id}'>{m.from_user.first_name}</a> لطفاً رعایت کن 🌸",
                    parse_mode="HTML"
                )
                time.sleep(3)
                bot.delete_message(m.chat.id, warn.id)
            except:
                pass
            break# ================= 🚫 سیستم بن / سکوت / اخطار =================

def bot_can_restrict(m):
    """بررسی اینکه ربات اجازه محدودسازی داره یا نه"""
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
    """دریافت آیدی کاربر هدف"""
    if m.reply_to_message:
        return m.reply_to_message.from_user.id
    parts = cmd_text(m).split()
    if len(parts) > 1 and parts[1].isdigit():
        return int(parts[1])
    return None

# 🚫 بن کاربر
@bot.message_handler(func=lambda m: cmd_text(m).startswith("بن"))
def ban_user(m):
    if not is_admin(m.chat.id, m.from_user.id) or not bot_can_restrict(m):
        return
    target = target_user(m)
    if not target:
        return bot.reply_to(m, "⚠️ لطفاً روی پیام کاربر ریپلای کن یا آیدی عددی بده.")
    if is_admin(m.chat.id, target) or is_sudo(target):
        return bot.reply_to(m, "😎 نمی‌تونی سودو یا مدیر رو بن کنی!")

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
        return bot.reply_to(m, "⚠️ نتونستم کاربر رو بن کنم. احتمالاً دسترسی ندارم.")
    bot.send_message(m.chat.id, f"🚫 <a href='tg://user?id={target}'>کاربر</a> بن شد ❌", parse_mode="HTML")

# ✅ حذف بن
@bot.message_handler(func=lambda m: cmd_text(m).startswith("حذف بن"))
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
    bot.send_message(m.chat.id, f"✅ <a href='tg://user?id={target}'>کاربر</a> از بن خارج شد 🌸", parse_mode="HTML")

# 🔇 سکوت
@bot.message_handler(func=lambda m: cmd_text(m).startswith("سکوت"))
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
    bot.send_message(m.chat.id, f"🔇 <a href='tg://user?id={target}'>کاربر</a> در سکوت قرار گرفت 💬", parse_mode="HTML")

# 🔊 حذف سکوت
@bot.message_handler(func=lambda m: cmd_text(m).startswith("حذف سکوت"))
def unmute_user(m):
    if not is_admin(m.chat.id, m.from_user.id) or not bot_can_restrict(m):
        return
    target = target_user(m)
    if not target:
        return bot.reply_to(m, "⚠️ روی پیام کاربر ریپلای کن یا آیدی بده.")
    d = load_data()
    gid = str(m.chat.id)
    if target not in d["muted"].get(gid, []):
        return bot.reply_to(m, "ℹ️ این کاربر در سکوت نیست.")
    d["muted"][gid].remove(target)
    save_data(d)
    bot.restrict_chat_member(m.chat.id, target, permissions=types.ChatPermissions(can_send_messages=True))
    bot.send_message(m.chat.id, f"🔊 سکوت از <a href='tg://user?id={target}'>کاربر</a> برداشته شد 🌼", parse_mode="HTML")

# ⚠️ اخطار
@bot.message_handler(func=lambda m: cmd_text(m).startswith("اخطار"))
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
    msg = f"⚠️ <a href='tg://user?id={target}'>کاربر</a> اخطار شماره <b>{count}</b> دریافت کرد ⚠️"
    if count >= 3:
        try:
            bot.ban_chat_member(m.chat.id, target)
            msg += "\n🚫 به دلیل ۳ اخطار بن شد."
            d["warns"][gid][str(target)] = 0
            save_data(d)
        except:
            msg += "\n⚠️ نتونستم بنش کنم (دسترسی محدود است)."
    bot.send_message(m.chat.id, msg, parse_mode="HTML")

# 📋 لیست‌ها
@bot.message_handler(func=lambda m: cmd_text(m) == "لیست بن")
def list_banned(m):
    d = load_data()
    lst = d["banned"].get(str(m.chat.id), [])
    if not lst:
        return bot.reply_to(m, "🚫 هیچ کاربری بن نشده.")
    text = "\n".join([f"• <a href='tg://user?id={x}'>کاربر {x}</a>" for x in lst])
    bot.reply_to(m, f"🚫 <b>لیست کاربران بن‌شده:</b>\n{text}", parse_mode="HTML")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست سکوت")
def list_muted(m):
    d = load_data()
    lst = d["muted"].get(str(m.chat.id), [])
    if not lst:
        return bot.reply_to(m, "🔇 هیچ کاربری در سکوت نیست.")
    text = "\n".join([f"• <a href='tg://user?id={x}'>کاربر {x}</a>" for x in lst])
    bot.reply_to(m, f"🔇 <b>لیست کاربران ساکت:</b>\n{text}", parse_mode="HTML")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست اخطار")
def list_warns(m):
    d = load_data()
    warns = d["warns"].get(str(m.chat.id), {})
    if not warns:
        return bot.reply_to(m, "⚠️ هیچ اخطاری ثبت نشده.")
    text = "\n".join([f"• <a href='tg://user?id={uid}'>کاربر {uid}</a> — {count} اخطار" for uid, count in warns.items()])
    bot.reply_to(m, f"⚠️ <b>لیست اخطارها:</b>\n{text}", parse_mode="HTML")

print("✅ بخش ۵ (بن / سکوت / اخطار) با موفقیت لود شد.")

# ================= 🚀 اجرای نهایی =================
if __name__ == "__main__":
    print("🤖 Persian Lux Panel V16 در حال اجراست...")

    while True:
        try:
            bot.infinity_polling(
                timeout=60,
                long_polling_timeout=40,
                skip_pending=True
            )
        except Exception as e:
            logging.error(f"⚠️ خطا در polling: {e}", exc_info=True)
            print(f"⚠️ خطا در polling: {e}")
            time.sleep(5)
