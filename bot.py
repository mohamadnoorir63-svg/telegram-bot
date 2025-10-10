# -*- coding: utf-8 -*-
# Persian Lux Panel V16 – Friendly Edition 😊
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
        "users": []
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

# ================= 🧰 ابزارها =================
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

print("✅ بخش ۱ (تنظیمات پایه + دیتا + ابزارها) با موفقیت لود شد.")# ================= 🆔 آیدی / آمار / ساعت / لینک‌ها =================

@bot.message_handler(func=lambda m: cmd_text(m) in ["آیدی", "ایدی"])
def show_id(m):
    """نمایش مشخصات کاربر با لحن دوستانه 😄"""
    try:
        user = m.from_user
        name = user.first_name or "ناشناس"
        uid = user.id
        caption = (
            f"👋 سلام {name}!\n\n"
            f"🆔 آیدی عددی‌ت: <code>{uid}</code>\n"
            f"💬 آیدی گروه: <code>{m.chat.id}</code>\n"
            f"📅 {shamsi_date()} | ⏰ {shamsi_time()}"
        )

        photos = bot.get_user_profile_photos(uid)
        if photos.total_count > 0:
            file_id = photos.photos[0][-1].file_id
            bot.send_photo(m.chat.id, file_id, caption=caption)
        else:
            bot.reply_to(m, caption)
    except:
        bot.reply_to(m, f"🆔 آیدی شما: <code>{m.from_user.id}</code>")

# 📊 آمار
@bot.message_handler(func=lambda m: cmd_text(m) == "آمار")
def show_stats(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    data = load_data()
    users = len(set(data.get("users", [])))
    groups = len(data.get("welcome", {}))
    bot.reply_to(
        m,
        f"📊 <b>آمار Persian Lux Panel</b>\n\n"
        f"👥 گروه‌ها: {groups}\n"
        f"👤 کاربران: {users}\n"
        f"📅 {shamsi_date()} | ⏰ {shamsi_time()}"
    )

# ⏰ ساعت
@bot.message_handler(func=lambda m: cmd_text(m) == "ساعت")
def show_time(m):
    bot.reply_to(m, f"⏰ ساعت الان: <b>{shamsi_time()}</b> 🕓")

# 🔗 لینک ربات
@bot.message_handler(func=lambda m: cmd_text(m) == "لینک ربات")
def bot_link(m):
    bot.reply_to(m, f"🤖 لینک دعوت من به گروه‌ها:\nhttps://t.me/{bot.get_me().username}")

# 📎 لینک گروه
@bot.message_handler(func=lambda m: cmd_text(m) == "لینک گروه")
def group_link(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return bot.reply_to(m, "🔐 فقط مدیرها می‌تونن لینک بگیرن.")
    try:
        link = bot.export_chat_invite_link(m.chat.id)
        bot.reply_to(m, f"🔗 لینک گروه:\n{link}")
    except:
        bot.reply_to(m, "⚠️ نمی‌تونم لینک بسازم، دسترسی لازمه!")

print("✅ بخش ۲ (آیدی، آمار، ساعت و لینک‌ها) با موفقیت لود شد.")# ================= 👋 سیستم خوشامد حرفه‌ای =================

@bot.message_handler(content_types=["new_chat_members"])
def welcome_new(m):
    """ارسال پیام خوشامد دوستانه برای عضو جدید 🌸"""
    data = load_data()
    gid = str(m.chat.id)
    data["welcome"].setdefault(gid, {"enabled": True, "type": "text", "content": None, "file_id": None})
    s = data["welcome"][gid]

    if not s.get("enabled", True):
        return  # خوشامد خاموش است

    user = m.new_chat_members[0]
    name = user.first_name or "دوست جدید"
    group_name = m.chat.title or "گروه"
    text = s.get("content") or f"🌟 سلام {name}!\nبه جمع دوستان در <b>{group_name}</b> خوش اومدی 😄"

    text = (
        text.replace("{name}", name)
        .replace("{group}", group_name)
        .replace("{time}", shamsi_time())
        .replace("{date}", shamsi_date())
    )

    if s.get("type") == "photo" and s.get("file_id"):
        bot.send_photo(m.chat.id, s["file_id"], caption=text)
    else:
        bot.send_message(m.chat.id, text)

# ================= ⚙️ تنظیمات خوشامد =================

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "خوشامد روشن")
def enable_welcome(m):
    data = load_data()
    gid = str(m.chat.id)
    data["welcome"].setdefault(gid, {})["enabled"] = True
    save_data(data)
    bot.reply_to(m, "✅ پیام خوشامد فعال شد. هرکس بیاد، بهش سلام گرم می‌دیم 😄")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "خوشامد خاموش")
def disable_welcome(m):
    data = load_data()
    gid = str(m.chat.id)
    data["welcome"].setdefault(gid, {})["enabled"] = False
    save_data(data)
    bot.reply_to(m, "🚫 خوشامد خاموش شد. دیگه کسیو خوش‌آمد نمی‌گیم 😅")

# ✏️ تنظیم خوشامد متنی
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "تنظیم خوشامد")
def set_welcome_text(m):
    txt = (m.reply_to_message.text or "").strip()
    if not txt:
        return bot.reply_to(m, "⚠️ لطفاً روی یک پیام متنی ریپلای کن تا همون متن بشه پیام خوشامد.")
    data = load_data()
    gid = str(m.chat.id)
    data["welcome"][gid] = {"enabled": True, "type": "text", "content": txt, "file_id": None}
    save_data(data)
    bot.reply_to(m, "💬 پیام خوشامد متنی با موفقیت تنظیم شد 🌟")

# 🖼️ تنظیم خوشامد تصویری
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "تنظیم خوشامد عکس")
def set_welcome_photo(m):
    if not m.reply_to_message.photo:
        return bot.reply_to(m, "⚠️ لطفاً روی پیام دارای عکس ریپلای کن.")
    file_id = m.reply_to_message.photo[-1].file_id
    caption = (m.reply_to_message.caption or "🌸 خوش اومدی {name} به {group} 😄").strip()
    data = load_data()
    gid = str(m.chat.id)
    data["welcome"][gid] = {"enabled": True, "type": "photo", "content": caption, "file_id": file_id}
    save_data(data)
    bot.reply_to(m, "🖼️ پیام خوشامد تصویری با موفقیت تنظیم شد ✅")

# 🔍 مشاهده پیام خوشامد فعلی
@bot.message_handler(func=lambda m: cmd_text(m) == "خوشامد")
def show_current_welcome(m):
    data = load_data()
    gid = str(m.chat.id)
    s = data["welcome"].get(gid)
    if not s:
        return bot.reply_to(m, "ℹ️ هنوز هیچ خوشامدی تنظیم نشده.")
    status = "✅ روشن" if s.get("enabled", True) else "🚫 خاموش"
    typ = "🖼️ تصویری" if s.get("type") == "photo" else "💬 متنی"
    msg = s.get("content") or "(خوشامد خالی)"
    bot.reply_to(
        m,
        f"📋 <b>وضعیت خوشامد</b>\n"
        f"وضعیت: {status}\n"
        f"نوع: {typ}\n\n"
        f"📄 متن:\n{msg}"
    )

print("✅ بخش ۳ (خوشامد حرفه‌ای و تنظیمات) با موفقیت لود شد.")# ================= 🔒 سیستم قفل‌ها =================

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

# 📌 فعال / غیرفعال کردن قفل‌ها
@bot.message_handler(func=lambda m: cmd_text(m).startswith("قفل ") or cmd_text(m).startswith("بازکردن "))
def toggle_lock(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return

    data = load_data()
    gid = str(m.chat.id)
    parts = cmd_text(m).split(" ", 1)
    if len(parts) < 2:
        return bot.reply_to(m, "⚠️ لطفاً بنویس مثلاً: قفل لینک یا بازکردن لینک")

    key_fa = parts[1]
    lock_type = LOCK_MAP.get(key_fa)
    if not lock_type:
        return bot.reply_to(m, "❌ نوع قفل نامعتبر است.")

    enable = cmd_text(m).startswith("قفل ")
    data["locks"].setdefault(gid, {k: False for k in LOCK_MAP.values()})
    data["locks"][gid][lock_type] = enable
    save_data(data)

    # اگر قفل گروه باشه (بستن چت)
    if lock_type == "گروه":
        try:
            perms = types.ChatPermissions(can_send_messages=not enable)
            bot.set_chat_permissions(m.chat.id, perms)
            msg = (
                "🚫 گروه بسته شد، فعلاً فقط مدیرها می‌تونن پیام بدن."
                if enable
                else "✅ گروه باز شد، همه می‌تونن چت کنن 🌸"
            )
            return bot.send_message(m.chat.id, msg)
        except:
            return bot.reply_to(m, "⚠️ خطایی در تغییر وضعیت چت رخ داد.")

    msg = (
        f"🔒 قفل {key_fa} فعال شد، ارسالش مجاز نیست 🚫"
        if enable
        else f"🔓 قفل {key_fa} غیرفعال شد، همه می‌تونن ازش استفاده کنن ✅"
    )
    bot.reply_to(m, msg)


# 🚫 کنترل خودکار پیام‌های ممنوعه
@bot.message_handler(content_types=[
    "text", "photo", "video", "sticker", "animation", "document", "audio", "voice"
])
def lock_filter(m):
    data = load_data()
    gid = str(m.chat.id)
    locks = data.get("locks", {}).get(gid, {})

    if not locks or is_admin(m.chat.id, m.from_user.id):
        return

    def warn(reason):
        try:
            bot.delete_message(m.chat.id, m.id)
        except:
            pass
        msg = bot.send_message(
            m.chat.id,
            f"🚨 لطفاً قوانین رو رعایت کن!\n{reason}\n"
            f"👤 <a href='tg://user?id={m.from_user.id}'>{m.from_user.first_name}</a>",
            parse_mode="HTML"
        )
        time.sleep(3)
        try:
            bot.delete_message(m.chat.id, msg.id)
        except:
            pass

    t = m.text or ""
    if locks.get("link") and any(x in t for x in ["http", "t.me/", "www."]):
        return warn("ارسال لینک در این گروه ممنوعه 🔗")
    if locks.get("photo") and m.content_type == "photo":
        return warn("ارسال عکس در این گروه مجاز نیست 🖼️")
    if locks.get("video") and m.content_type == "video":
        return warn("ارسال ویدیو در این گروه مجاز نیست 🎬")
    if locks.get("sticker") and m.content_type == "sticker":
        return warn("استفاده از استیکر در این گروه ممنوعه 🧸")
    if locks.get("gif") and m.content_type == "animation":
        return warn("ارسال گیف در این گروه بسته شده 🎞️")
    if locks.get("file") and m.content_type == "document":
        return warn("ارسال فایل در این گروه مجاز نیست 📁")
    if locks.get("music") and m.content_type == "audio":
        return warn("ارسال آهنگ در این گروه ممنوعه 🎵")
    if locks.get("voice") and m.content_type == "voice":
        return warn("ارسال ویس در این گروه مجاز نیست 🎤")
    if locks.get("text") and m.text:
        return warn("ارسال پیام متنی فعلاً بسته است 💬")

print("✅ بخش ۴ (سیستم قفل‌ها) با موفقیت لود شد.")# ================= 🚫 مدیریت کاربران (بن / سکوت / اخطار) =================

def ensure_data_keys():
    """ایجاد کلیدهای مورد نیاز در فایل دیتا"""
    d = load_data()
    for key in ["banned", "muted", "warns"]:
        if key not in d:
            d[key] = {}
    save_data(d)

def get_target_id(m):
    """گرفتن آیدی هدف از ریپلای یا دستور"""
    parts = cmd_text(m).split()
    if m.reply_to_message:
        return m.reply_to_message.from_user.id
    elif len(parts) > 1 and parts[1].isdigit():
        return int(parts[1])
    return None

# 🚫 بن کاربر
@bot.message_handler(func=lambda m: cmd_text(m).startswith("بن"))
def ban_user(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    target = get_target_id(m)
    if not target:
        return bot.reply_to(m, "⚠️ لطفاً روی پیام کاربر ریپلای کن یا آیدیش رو بنویس.\nمثال: بن 123456789")

    if is_sudo(target):
        return bot.reply_to(m, "😅 نمی‌تونم سودو رو بن کنم، اون بالاسری منه!")

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
    bot.reply_to(m, f"🚫 <a href='tg://user?id={target}'>کاربر</a> از گروه بن شد ❌", parse_mode="HTML")

# 🔓 حذف بن
@bot.message_handler(func=lambda m: cmd_text(m).startswith("حذف بن"))
def unban_user(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    target = get_target_id(m)
    if not target:
        return bot.reply_to(m, "⚠️ روی پیام ریپلای کن یا آیدی بده.\nمثال: حذف بن 123456789")

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
    bot.reply_to(m, f"✅ <a href='tg://user?id={target}'>کاربر</a> از لیست بن خارج شد 🌿", parse_mode="HTML")

# 🔇 سکوت
@bot.message_handler(func=lambda m: cmd_text(m).startswith("سکوت"))
def mute_user(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    target = get_target_id(m)
    if not target:
        return bot.reply_to(m, "⚠️ لطفاً ریپلای کن یا آیدی بده.")
    gid = str(m.chat.id)
    ensure_data_keys()
    d = load_data()
    d["muted"].setdefault(gid, [])
    if target in d["muted"][gid]:
        return bot.reply_to(m, "ℹ️ این کاربر از قبل در حالت سکوت است.")
    d["muted"][gid].append(target)
    save_data(d)
    try:
        perms = types.ChatPermissions(can_send_messages=False)
        bot.restrict_chat_member(m.chat.id, target, permissions=perms)
    except:
        pass
    bot.reply_to(m, f"🔇 <a href='tg://user?id={target}'>کاربر</a> ساکت شد 😶", parse_mode="HTML")

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
    bot.reply_to(m, f"🔊 سکوت <a href='tg://user?id={target}'>کاربر</a> برداشته شد 😄", parse_mode="HTML")

# ⚠️ اخطار
@bot.message_handler(func=lambda m: cmd_text(m).startswith("اخطار"))
def warn_user(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    target = get_target_id(m)
    if not target:
        return bot.reply_to(m, "⚠️ لطفاً روی پیام ریپلای کن یا آیدی بده.")
    gid = str(m.chat.id)
    ensure_data_keys()
    d = load_data()
    d["warns"].setdefault(gid, {})
    d["warns"][gid][str(target)] = d["warns"][gid].get(str(target), 0) + 1
    save_data(d)
    count = d["warns"][gid][str(target)]
    msg = f"⚠️ <a href='tg://user?id={target}'>کاربر</a> اخطار شماره {count} گرفت 😬"
    if count >= 3:
        bot.ban_chat_member(m.chat.id, target)
        msg += "\n🚫 چون ۳ اخطار گرفت، از گروه حذف شد ❌"
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
    bot.reply_to(m, f"✅ همه اخطارهای <a href='tg://user?id={target}'>کاربر</a> پاک شد 🌸", parse_mode="HTML")

# 📋 لیست‌ها
@bot.message_handler(func=lambda m: cmd_text(m) == "لیست بن")
def list_ban(m):
    d = load_data()
    gid = str(m.chat.id)
    lst = d.get("banned", {}).get(gid, [])
    if not lst:
        return bot.reply_to(m, "🚫 هیچ کاربری بن نشده 😇")
    text = "\n".join([f"• <a href='tg://user?id={x}'>کاربر {x}</a>" for x in lst])
    bot.reply_to(m, f"🚫 <b>لیست کاربران بن‌شده:</b>\n{text}", parse_mode="HTML")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست سکوت")
def list_mute(m):
    d = load_data()
    gid = str(m.chat.id)
    lst = d.get("muted", {}).get(gid, [])
    if not lst:
        return bot.reply_to(m, "🔇 هیچ کاربری در حالت سکوت نیست 😌")
    text = "\n".join([f"• <a href='tg://user?id={x}'>کاربر {x}</a>" for x in lst])
    bot.reply_to(m, f"🔇 <b>لیست کاربران ساکت:</b>\n{text}", parse_mode="HTML")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست اخطار")
def list_warn(m):
    d = load_data()
    gid = str(m.chat.id)
    warns = d.get("warns", {}).get(gid, {})
    if not warns:
        return bot.reply_to(m, "⚠️ هیچ اخطاری ثبت نشده 🌿")
    text = "\n".join([f"• <a href='tg://user?id={x}'>کاربر {x}</a> — {warns[x]} اخطار" for x in warns])
    bot.reply_to(m, f"⚠️ <b>لیست اخطارها:</b>\n{text}", parse_mode="HTML")

print("✅ بخش ۵ (بن / سکوت / اخطار / لیست‌ها) با موفقیت لود شد.")
# ================= 🚀 اجرای نهایی =================
if __name__ == "__main__":
    print("🤖 Persian Lux Panel V16 در حال اجراست...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=40, skip_pending=True)
        except Exception as e:
            logging.error(f"polling crash: {e}")
            time.sleep(5)
