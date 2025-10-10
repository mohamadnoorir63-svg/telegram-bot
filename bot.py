# -*- coding: utf-8 -*-
# Persian Lux Panel V17 – Final Pro (Only Groups)
# Designed for Mohammad 👑

import os
import json
import time
import logging
from datetime import datetime
import telebot
from telebot import types

# -------------------- Optional Jalali (no-crash fallback) --------------------
try:
    import jdatetime
    def shamsi_date():
        return jdatetime.datetime.now().strftime("%A %d %B %Y")
    def shamsi_time():
        return jdatetime.datetime.now().strftime("%H:%M:%S")
    JALALI_OK = True
except Exception:
    # اگر jdatetime نصب نبود، با میلادی ادامه می‌دهیم تا برنامه کرش نکند
    def shamsi_date():
        return datetime.now().strftime("%A %d %B %Y")
    def shamsi_time():
        return datetime.now().strftime("%H:%M:%S")
    JALALI_OK = False

# ================= ⚙️ تنظیمات پایه =================
TOKEN = os.environ.get("BOT_TOKEN")  # حتماً در Config Vars تنظیم کن
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))  # آیدی عددی اصلی شما

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
        "welcome": {},      # per-group: {gid: {enabled, type, content, file_id}}
        "locks": {},        # per-group: {gid: {lock_key: bool}}
        "admins": {},       # per-group: {gid: [user_ids]}
        "sudo_list": [],    # global extra sudo user ids (as str)
        "banned": {},       # per-group: {gid: [user_ids]}
        "muted": {},        # per-group: {gid: [user_ids]}
        "warns": {},        # per-group: {gid: {uid(str): count}}
        "filters": {},      # per-group: {gid: [words]}
        "users": []         # global users seen
    }

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(base_data())
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = base_data()
    # ensure keys
    template = base_data()
    for k in template:
        if k not in data:
            data[k] = template[k]
    save_data(data)
    return data

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def ensure_group_struct(gid):
    d = load_data()
    gid = str(gid)
    d["welcome"].setdefault(gid, {"enabled": True, "type": "text", "content": None, "file_id": None})
    d["locks"].setdefault(gid, {
        k: False for k in ["link","group","photo","video","sticker","gif","file","music","voice","forward","text"]
    })
    d["admins"].setdefault(gid, [])
    d["banned"].setdefault(gid, [])
    d["muted"].setdefault(gid, [])
    d["warns"].setdefault(gid, {})
    d["filters"].setdefault(gid, [])
    save_data(d)

# ================= 🧰 ابزارها =================
def cmd_text(m):
    return (getattr(m, "text", None) or "").strip()

def first_word(m):
    t = cmd_text(m)
    return t.split()[0] if t else ""

def in_group(m):
    # فقط در گروه‌ها کار کنه
    return getattr(m.chat, "type", "") in ("group", "supergroup")

def is_sudo(uid):
    d = load_data()
    return str(uid) in [str(SUDO_ID)] + d.get("sudo_list", [])

def is_admin(chat_id, uid):
    # سودو یا مدیر تلگرام یا مدیر سفارشی گروه
    if is_sudo(uid):
        return True
    try:
        st = bot.get_chat_member(chat_id, uid)
        if st.status in ("administrator", "creator"):
            return True
    except:
        pass
    d = load_data()
    return str(uid) in list(map(str, d["admins"].get(str(chat_id), [])))

def bot_admin_perms(chat_id):
    """بررسی دسترسی‌های ربات در گروه (برای بن/سکوت/بازکردن چت و …)"""
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
        return {"is_admin": False, "can_restrict": False, "can_delete": False,
                "can_invite": False, "can_change_info": False, "can_manage_chat": False}

def get_target_id(m):
    parts = cmd_text(m).split()
    if m.reply_to_message:
        return m.reply_to_message.from_user.id
    elif len(parts) > 1 and parts[1].isdigit():
        return int(parts[1])
    return None

def short_name(u):
    return (u.first_name or "کاربر").strip()

# ================= 🆔 آیدی / آمار / ساعت / لینک‌ها =================
@bot.message_handler(func=lambda m: in_group(m) and cmd_text(m) in ["آیدی", "ایدی"])
def show_id(m):
    try:
        user = m.from_user
        caption = (
            f"🧾 <b>مشخصات</b>\n"
            f"👤 نام: {short_name(user)}\n"
            f"🆔 آیدی: <code>{user.id}</code>\n"
            f"💬 آیدی گروه: <code>{m.chat.id}</code>\n"
            f"📅 {shamsi_date()} | ⏰ {shamsi_time()}"
        )
        photos = bot.get_user_profile_photos(user.id)
        if getattr(photos, "total_count", 0) > 0:
            file_id = photos.photos[0][-1].file_id
            bot.send_photo(m.chat.id, file_id, caption=caption)
        else:
            bot.reply_to(m, caption)
    except:
        bot.reply_to(m, f"🆔 <code>{m.from_user.id}</code>")

@bot.message_handler(func=lambda m: in_group(m) and cmd_text(m) == "آمار")
def stats(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    d = load_data()
    users = len(set(d.get("users", [])))
    groups = len(d.get("welcome", {}))
    bot.reply_to(m, f"📊 <b>آمار</b>\n👥 گروه‌ها: {groups}\n👤 کاربران: {users}\n⏰ {shamsi_time()}")

@bot.message_handler(func=lambda m: in_group(m) and cmd_text(m) == "ساعت")
def show_time(m):
    bot.reply_to(m, f"⏰ {shamsi_time()} | 📅 {shamsi_date()}")

@bot.message_handler(func=lambda m: in_group(m) and cmd_text(m) == "لینک ربات")
def bot_link(m):
    try:
        bot.reply_to(m, f"🤖 https://t.me/{bot.get_me().username}")
    except:
        bot.reply_to(m, "⚠️ نتونستم یوزرنیم خودمو بگیرم.")

@bot.message_handler(func=lambda m: in_group(m) and cmd_text(m) == "لینک گروه")
def group_link(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    if not bot_admin_perms(m.chat.id)["is_admin"]:
        return bot.reply_to(m, "⚠️ من ادمین گروه نیستم تا لینک بسازم.")
    try:
        link = bot.export_chat_invite_link(m.chat.id)
        bot.reply_to(m, f"🔗 لینک گروه:\n{link}")
    except Exception as e:
        bot.reply_to(m, f"⚠️ دسترسی ساخت لینک ندارم.\n<code>{e}</code>")

# ================= 📖 راهنما =================
HELP_TEXT = (
    "📖 <b>راهنما</b>\n"
    "— فقط در گروه فعال است —\n\n"
    "🆔 اطلاعات: آیدی | آمار | ساعت | لینک ربات | لینک گروه\n"
    "👋 خوشامد: خوشامد روشن / خاموش | تنظیم خوشامد (ریپلای) | تنظیم خوشامد عکس (ریپلای) | خوشامد\n"
    "🔒 قفل‌ها: قفل لینک/عکس/ویدیو/استیکر/گیف/فایل/موزیک/ویس/متن/فوروارد/گروه\n"
    "           بازکردن لینک/…/گروه\n"
    "🚫 مدیریت: بن (ریپلای/آیدی) | حذف بن | سکوت | حذف سکوت | اخطار | حذف اخطار\n"
    "📋 لیست‌ها: لیست بن | لیست سکوت | لیست اخطار | لیست فیلتر | لیست مدیر\n"
    "🧩 فیلتر کلمه: افزودن فیلتر <کلمه> | حذف فیلتر <کلمه>\n"
    "🛡️ مدیریت مدیرها: افزودن مدیر (ریپلای/آیدی) | حذف مدیر | لیست مدیر\n"
    "👑 مدیریت سودو (فقط صاحب ربات): افزودن سودو (ریپلای/آیدی) | حذف سودو | لیست سودو\n"
)

@bot.message_handler(func=lambda m: in_group(m) and cmd_text(m) in ["راهنما","help","Help"])
def help_cmd(m):
    bot.reply_to(m, HELP_TEXT)

# ================= 👋 خوشامد =================
@bot.message_handler(content_types=["new_chat_members"])
def welcome_new(m):
    if not in_group(m): 
        return
    ensure_group_struct(m.chat.id)
    d = load_data()
    s = d["welcome"][str(m.chat.id)]
    if not s.get("enabled", True):
        return
    user = m.new_chat_members[0]
    name = user.first_name or "دوست جدید"
    group_name = m.chat.title or "گروه"
    text = s.get("content") or f"✨ سلام {name}!\nبه <b>{group_name}</b> خوش اومدی 🌸"
    text = (text.replace("{name}", name)
                .replace("{group}", group_name)
                .replace("{time}", shamsi_time())
                .replace("{date}", shamsi_date()))
    if s.get("type") == "photo" and s.get("file_id"):
        bot.send_photo(m.chat.id, s["file_id"], caption=text)
    else:
        bot.send_message(m.chat.id, text)

@bot.message_handler(func=lambda m: in_group(m) and is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "خوشامد روشن")
def enable_welcome(m):
    ensure_group_struct(m.chat.id)
    d = load_data()
    d["welcome"][str(m.chat.id)]["enabled"] = True
    save_data(d)
    bot.reply_to(m, "✅ خوشامد فعال شد.")

@bot.message_handler(func=lambda m: in_group(m) and is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "خوشامد خاموش")
def disable_welcome(m):
    ensure_group_struct(m.chat.id)
    d = load_data()
    d["welcome"][str(m.chat.id)]["enabled"] = False
    save_data(d)
    bot.reply_to(m, "🚫 خوشامد خاموش شد.")

@bot.message_handler(func=lambda m: in_group(m) and is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "تنظیم خوشامد")
def set_welcome_text(m):
    txt = (m.reply_to_message.text or "").strip()
    if not txt:
        return bot.reply_to(m, "⚠️ روی یک پیام متنی ریپلای کن.")
    ensure_group_struct(m.chat.id)
    d = load_data()
    d["welcome"][str(m.chat.id)] = {"enabled": True, "type": "text", "content": txt, "file_id": None}
    save_data(d)
    bot.reply_to(m, "💬 پیام خوشامد متنی تنظیم شد.")

@bot.message_handler(func=lambda m: in_group(m) and is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "تنظیم خوشامد عکس")
def set_welcome_photo(m):
    if not m.reply_to_message.photo:
        return bot.reply_to(m, "⚠️ روی یک پیامِ دارای عکس ریپلای کن.")
    file_id = m.reply_to_message.photo[-1].file_id
    caption = (m.reply_to_message.caption or "🌸 خوش اومدی {name} به {group}").strip()
    ensure_group_struct(m.chat.id)
    d = load_data()
    d["welcome"][str(m.chat.id)] = {"enabled": True, "type": "photo", "content": caption, "file_id": file_id}
    save_data(d)
    bot.reply_to(m, "🖼️ خوشامد تصویری تنظیم شد.")

@bot.message_handler(func=lambda m: in_group(m) and cmd_text(m) == "خوشامد")
def show_welcome(m):
    ensure_group_struct(m.chat.id)
    d = load_data()
    s = d["welcome"][str(m.chat.id)]
    status = "✅ روشن" if s.get("enabled", True) else "🚫 خاموش"
    typ = "🖼️ تصویری" if s.get("type") == "photo" else "💬 متنی"
    msg = s.get("content") or "(خالی)"
    bot.reply_to(m, f"📋 <b>وضعیت خوشامد</b>\nوضعیت: {status}\nنوع: {typ}\n\n📄 متن:\n{msg}")

# ================= 🛡️ مدیریت مدیرها و سودو =================
@bot.message_handler(func=lambda m: in_group(m) and is_admin(m.chat.id, m.from_user.id) and first_word(m) == "افزودن" and "مدیر" in cmd_text(m))
def add_admin(m):
    ensure_group_struct(m.chat.id)
    target = get_target_id(m)
    if not target:
        return bot.reply_to(m, "⚠️ روی پیام شخص ریپلای کن یا آیدی بنویس.")
    d = load_data()
    arr = d["admins"].setdefault(str(m.chat.id), [])
    if target in arr:
        return bot.reply_to(m, "ℹ️ این کاربر از قبل مدیر سفارشی است.")
    arr.append(target)
    save_data(d)
    bot.reply_to(m, "✅ مدیر اضافه شد.")

@bot.message_handler(func=lambda m: in_group(m) and is_admin(m.chat.id, m.from_user.id) and first_word(m) == "حذف" and "مدیر" in cmd_text(m))
def del_admin(m):
    ensure_group_struct(m.chat.id)
    target = get_target_id(m)
    if not target:
        return bot.reply_to(m, "⚠️ ریپلای یا آیدی بده.")
    d = load_data()
    arr = d["admins"].setdefault(str(m.chat.id), [])
    if target in arr:
        arr.remove(target)
        save_data(d)
        return bot.reply_to(m, "✅ مدیر حذف شد.")
    bot.reply_to(m, "ℹ️ این کاربر مدیر سفارشی نبود.")

@bot.message_handler(func=lambda m: in_group(m) and cmd_text(m) == "لیست مدیر")
def list_admins(m):
    d = load_data()
    lst = d["admins"].get(str(m.chat.id), [])
    if not lst:
        return bot.reply_to(m, "ℹ️ هیچ مدیر سفارشی ثبت نشده.")
    text = "\n".join([f"• <a href='tg://user?id={x}'>کاربر {x}</a>" for x in lst])
    bot.reply_to(m, f"🛡️ <b>لیست مدیرهای سفارشی:</b>\n{text}", parse_mode="HTML")

@bot.message_handler(func=lambda m: in_group(m) and is_sudo(m.from_user.id) and first_word(m) == "افزودن" and "سودو" in cmd_text(m))
def add_sudo(m):
    d = load_data()
    target = get_target_id(m)
    if not target:
        return bot.reply_to(m, "⚠️ ریپلای/آیدی بده.")
    arr = set(map(str, d.get("sudo_list", [])))
    arr.add(str(target))
    d["sudo_list"] = list(arr)
    save_data(d)
    bot.reply_to(m, "👑 سودو اضافه شد.")

@bot.message_handler(func=lambda m: in_group(m) and is_sudo(m.from_user.id) and first_word(m) == "حذف" and "سودو" in cmd_text(m))
def del_sudo(m):
    d = load_data()
    target = get_target_id(m)
    if not target:
        return bot.reply_to(m, "⚠️ ریپلای/آیدی بده.")
    arr = list(map(str, d.get("sudo_list", [])))
    if str(target) in arr:
        arr.remove(str(target))
        d["sudo_list"] = arr
        save_data(d)
        return bot.reply_to(m, "✅ سودو حذف شد.")
    bot.reply_to(m, "ℹ️ این کاربر در لیست سودو نبود.")

@bot.message_handler(func=lambda m: in_group(m) and is_sudo(m.from_user.id) and cmd_text(m) == "لیست سودو")
def list_sudo(m):
    d = load_data()
    arr = d.get("sudo_list", [])
    if not arr:
        return bot.reply_to(m, "ℹ️ هیچ سودویی ثبت نشده.")
    text = "\n".join([f"• <a href='tg://user?id={x}'>کاربر {x}</a>" for x in arr])
    bot.reply_to(m, f"👑 <b>لیست سودو:</b>\n{text}", parse_mode="HTML")

# ================= 🔒 قفل‌ها =================
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
    "گروه": "group",
}

@bot.message_handler(func=lambda m: in_group(m) and (cmd_text(m).startswith("قفل ") or cmd_text(m).startswith("بازکردن ")))
def toggle_lock(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    ensure_group_struct(m.chat.id)
    d = load_data()
    gid = str(m.chat.id)
    parts = cmd_text(m).split(" ", 1)
    if len(parts) < 2:
        return bot.reply_to(m, "⚠️ مثال: قفل لینک / بازکردن لینک")
    key_fa = parts[1].strip()
    lock_key = LOCK_MAP.get(key_fa)
    if not lock_key:
        return bot.reply_to(m, "❌ نوع قفل نامعتبر است.")
    enable = cmd_text(m).startswith("قفل ")
    d["locks"][gid][lock_key] = enable
    save_data(d)

    # بستن/بازکردن چت
    if lock_key == "group":
        perms = bot_admin_perms(m.chat.id)
        if not perms["is_admin"]:
            return bot.reply_to(m, "⚠️ من ادمین نیستم که گروه رو ببندم/باز کنم.")
        try:
            p = types.ChatPermissions(can_send_messages=not enable)
            bot.set_chat_permissions(m.chat.id, p)
            if enable:
                bot.send_message(m.chat.id, f"🚫 گروه بسته شد. ⏰ {shamsi_time()}")
            else:
                bot.send_message(m.chat.id, f"✅ گروه باز شد. ⏰ {shamsi_time()}")
        except Exception as e:
            bot.reply_to(m, f"⚠️ خطا در تغییر وضعیت گروه:\n<code>{e}</code>")
        return

    msg = f"🔒 قفل {key_fa} فعال شد." if enable else f"🔓 قفل {key_fa} غیرفعال شد."
    bot.reply_to(m, msg)

# ================= 🧩 فیلتر کلمه =================
@bot.message_handler(func=lambda m: in_group(m) and cmd_text(m).startswith("افزودن فیلتر "))
def add_filter(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    ensure_group_struct(m.chat.id)
    word = cmd_text(m).split(" ", 2)[2].strip() if len(cmd_text(m).split(" ", 2)) >= 3 else ""
    if not word:
        return bot.reply_to(m, "⚠️ مثال: افزودن فیلتر سلام")
    d = load_data()
    arr = d["filters"].setdefault(str(m.chat.id), [])
    if word in arr:
        return bot.reply_to(m, "ℹ️ قبلاً همین فیلتر ثبت شده.")
    arr.append(word)
    save_data(d)
    bot.reply_to(m, f"✅ فیلتر «{word}» اضافه شد.")

@bot.message_handler(func=lambda m: in_group(m) and cmd_text(m).startswith("حذف فیلتر "))
def del_filter(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    ensure_group_struct(m.chat.id)
    word = cmd_text(m).split(" ", 2)[2].strip() if len(cmd_text(m).split(" ", 2)) >= 3 else ""
    if not word:
        return bot.reply_to(m, "⚠️ مثال: حذف فیلتر سلام")
    d = load_data()
    arr = d["filters"].setdefault(str(m.chat.id), [])
    if word in arr:
        arr.remove(word)
        save_data(d)
        return bot.reply_to(m, f"✅ فیلتر «{word}» حذف شد.")
    bot.reply_to(m, "ℹ️ چنین فیلتری ثبت نشده بود.")

@bot.message_handler(func=lambda m: in_group(m) and cmd_text(m) == "لیست فیلتر")
def list_filters(m):
    d = load_data()
    arr = d["filters"].get(str(m.chat.id), [])
    if not arr:
        return bot.reply_to(m, "ℹ️ هیچ فیلتری ثبت نشده.")
    bot.reply_to(m, "🧩 <b>فیلترها:</b>\n" + "\n".join([f"• {w}" for w in arr]))

# ================= 🚫 کنترل خودکار (قفل‌ها + فیلتر + سکوت) =================
@bot.message_handler(content_types=["text","photo","video","sticker","animation","document","audio","voice","forward"])
def auto_moderate(m):
    if not in_group(m):
        return
    ensure_group_struct(m.chat.id)
    d = load_data()
    gid = str(m.chat.id)

    # ثبت کاربر برای آمار
    try:
        users = set(map(int, d.get("users", [])))
        users.add(int(m.from_user.id))
        d["users"] = list(users)
        save_data(d)
    except:
        pass

    # اگر کاربر ساکت است، پیام را حذف کن
    if str(m.from_user.id) in list(map(str, d["muted"].get(gid, []))):
        try: bot.delete_message(m.chat.id, m.id)
        except: pass
        return

    # مدیرها و سودو آزادند
    if is_admin(m.chat.id, m.from_user.id):
        return

    locks = d["locks"].get(gid, {})
    def warn_and_delete(reason):
        try:
            bot.delete_message(m.chat.id, m.id)
        except: pass
        try:
            msg = bot.send_message(
                m.chat.id,
                f"🚨 لطفاً قوانین رو رعایت کن!\n{reason}\n"
                f"👤 <a href='tg://user?id={m.from_user.id}'>{short_name(m.from_user)}</a>",
                parse_mode="HTML"
            )
            time.sleep(3)
            bot.delete_message(m.chat.id, msg.id)
        except:
            pass

    # قفل‌ها
    text_lower = (m.text or "").lower()
    if locks.get("link") and any(x in text_lower for x in ["http", "www.", "t.me/","telegram.me/"]):
        return warn_and_delete("🔗 ارسال لینک ممنوع است.")
    if locks.get("text") and m.text:
        return warn_and_delete("💬 ارسال متن ممنوع است.")
    if locks.get("photo") and m.content_type == "photo":
        return warn_and_delete("🖼️ ارسال عکس ممنوع است.")
    if locks.get("video") and m.content_type == "video":
        return warn_and_delete("🎬 ارسال ویدیو ممنوع است.")
    if locks.get("sticker") and m.content_type == "sticker":
        return warn_and_delete("🧸 ارسال استیکر ممنوع است.")
    if locks.get("gif") and m.content_type == "animation":
        return warn_and_delete("🎞️ ارسال گیف ممنوع است.")
    if locks.get("file") and m.content_type == "document":
        return warn_and_delete("📁 ارسال فایل ممنوع است.")
    if locks.get("music") and m.content_type == "audio":
        return warn_and_delete("🎵 ارسال موزیک ممنوع است.")
    if locks.get("voice") and m.content_type == "voice":
        return warn_and_delete("🎤 ارسال ویس ممنوع است.")
    if locks.get("forward") and (m.forward_from or m.forward_from_chat):
        return warn_and_delete("🔁 فوروارد ممنوع است.")

    # فیلتر کلمه
    flt = d["filters"].get(gid, [])
    if m.text and flt:
        for w in flt:
    
