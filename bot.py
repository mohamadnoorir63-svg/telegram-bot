# -*- coding: utf-8 -*-
import os, json, random
from datetime import datetime, timedelta
import pytz, jdatetime
import telebot
from telebot import types

# ================= ⚙️ تنظیمات اولیه =================
TOKEN = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
DATA_FILE = "data.json"

# ================= 📁 ساختار ذخیره داده =================
def base_data():
    return {
        "welcome": {},
        "locks": {},
        "admins": {},
        "sudo_list": [],
        "banned": {},
        "muted": {},
        "jokes": [],
        "falls": [],
        "users": [],
        "stats": {}  # آمار روزانه گروه‌ها
    }

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(base_data())
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except:
            data = base_data()
    for k, v in base_data().items():
        if k not in data:
            data[k] = v
    save_data(data)
    return data

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def register_group(gid):
    data = load_data()
    gid = str(gid)
    data["welcome"].setdefault(gid, {"enabled": True, "type": "text", "content": None, "file_id": None})
    data["locks"].setdefault(gid, {k: False for k in LOCK_MAP.values()})
    data["stats"].setdefault(gid, make_stats())
    save_data(data)

# ================= 🧩 ابزارهای کمکی =================
def cmd_text(m): return (getattr(m, "text", None) or "").strip()
def now_teh(): return datetime.now(pytz.timezone("Asia/Tehran"))
def now_str(): return now_teh().strftime("%H:%M:%S")
def shamsi_date(): return jdatetime.datetime.now().strftime("%A %d %B %Y")

def is_sudo(uid):
    d = load_data()
    return str(uid) in [str(SUDO_ID)] + d.get("sudo_list", [])

def is_admin(chat_id, uid):
    d = load_data()
    if is_sudo(uid): return True
    gid = str(chat_id)
    if str(uid) in d["admins"].get(gid, []): return True
    try:
        st = bot.get_chat_member(chat_id, uid).status
        return st in ("administrator", "creator")
    except: return False

# ================= 🔒 تعریف قفل‌ها =================
LOCK_MAP = {
    "لینک": "link", "گروه": "group", "عکس": "photo", "ویدیو": "video",
    "استیکر": "sticker", "گیف": "gif", "فایل": "file",
    "موزیک": "music", "ویس": "voice", "فوروارد": "forward"
}

# ================= 📊 آمار روزانه =================
def make_stats():
    return {
        "messages": 0, "photo": 0, "video": 0, "voice": 0,
        "music": 0, "gif": 0, "sticker": 0, "forward": 0,
        "top_users": {}, "last_reset": now_teh().strftime("%Y-%m-%d")
    }

def reset_stats_if_needed(gid):
    data = load_data()
    today = now_teh().strftime("%Y-%m-%d")
    if data["stats"].get(gid, {}).get("last_reset") != today:
        data["stats"][gid] = make_stats()
        save_data(data)

def add_activity(gid, uid, kind):
    data = load_data()
    gid = str(gid)
    reset_stats_if_needed(gid)
    s = data["stats"][gid]
    s["messages"] += 1
    if kind in s: s[kind] += 1
    s["top_users"][str(uid)] = s["top_users"].get(str(uid), 0) + 1
    save_data(data)

def format_stats(gid):
    data = load_data()
    s = data["stats"].get(str(gid), make_stats())
    sorted_users = sorted(s["top_users"].items(), key=lambda x: x[1], reverse=True)
    top_user = f"( {sorted_users[0][1]} پیام | {sorted_users[0][0]} )" if sorted_users else "هیچ فعالیتی ثبت نشده است!"
    return (
f"♡ فعالیت های امروز تا این لحظه :\n"
f"➲ تاریخ : {shamsi_date()}\n"
f"➲ ساعت : {now_str()}\n"
f"✛ کل پیام ها : {s['messages']}\n"
f"✛ عکس : {s['photo']}\n"
f"✛ ویدیو : {s['video']}\n"
f"✛ موزیک : {s['music']}\n"
f"✛ ویس : {s['voice']}\n"
f"✛ گیف : {s['gif']}\n"
f"✛ استیکر : {s['sticker']}\n"
f"✛ پیام فورواردی : {s['forward']}\n"
f"✶ فعال ترین اعضای گروه:\n• نفر اول🥇 : {top_user}"
)

# ================= 💬 دستورات عمومی =================
@bot.message_handler(func=lambda m: cmd_text(m) in ["آیدی","ایدی"])
def cmd_id(m):
    try:
        photos = bot.get_user_profile_photos(m.from_user.id, limit=1)
        caption = (
            f"🆔 شناسه شما: <code>{m.from_user.id}</code>\n"
            f"🆔 شناسه گروه: <code>{m.chat.id}</code>\n"
            f"📅 تاریخ: {shamsi_date()}\n"
            f"⏰ ساعت: {now_str()}"
        )
        if photos.total_count > 0:
            bot.send_photo(m.chat.id, photos.photos[0][-1].file_id, caption=caption)
        else:
            bot.reply_to(m, caption)
    except:
        bot.reply_to(m, "❗ خطا در دریافت آیدی")

@bot.message_handler(func=lambda m: cmd_text(m) == "ساعت")
def cmd_time(m):
    bot.reply_to(m, f"⏰ تهران: {now_str()}\n📅 شمسی: {shamsi_date()}")

@bot.message_handler(func=lambda m: cmd_text(m) == "آمار")
def cmd_stats(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    bot.reply_to(m, format_stats(m.chat.id))

# ================= 🎉 خوشامد =================
@bot.message_handler(content_types=["new_chat_members"])
def welcome_new(m):
    register_group(m.chat.id)
    d = load_data(); gid = str(m.chat.id)
    s = d["welcome"][gid]
    if not s.get("enabled", True): return
    name = m.new_chat_members[0].first_name
    text = s.get("content") or f"سلام {name} 🌸\nبه {m.chat.title} خوش اومدی! 🌙"
    text = text.replace("{name}", name).replace("{time}", f"{now_str()} - {shamsi_date()}")
    if s.get("type") == "photo" and s.get("file_id"):
        bot.send_photo(m.chat.id, s["file_id"], caption=text)
    else:
        bot.send_message(m.chat.id, text)

@bot.message_handler(func=lambda m: cmd_text(m) in ["خوشامد روشن","خوشامد خاموش"])
def toggle_welcome(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    d = load_data(); gid = str(m.chat.id)
    en = cmd_text(m) == "خوشامد روشن"
    d["welcome"].setdefault(gid, {"enabled": True})
    d["welcome"][gid]["enabled"] = en
    save_data(d)
    bot.reply_to(m, "✅ خوشامد روشن شد" if en else "🚫 خوشامد خاموش شد")

@bot.message_handler(func=lambda m: cmd_text(m) == "تنظیم خوشامد" and m.reply_to_message)
def set_welcome(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    d = load_data(); gid = str(m.chat.id)
    if m.reply_to_message.photo:
        d["welcome"][gid] = {"enabled": True, "type": "photo", "file_id": m.reply_to_message.photo[-1].file_id,
                             "content": m.reply_to_message.caption or ""}
    else:
        d["welcome"][gid] = {"enabled": True, "type": "text", "content": m.reply_to_message.text}
    save_data(d)
    bot.reply_to(m, "🎉 خوشامد تنظیم شد.")

# ================= 👑 مدیریت سودو و مدیر =================
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "افزودن سودو")
def add_sudo(m):
    if m.from_user.id != SUDO_ID: return
    d = load_data(); uid = str(m.reply_to_message.from_user.id)
    if uid in d["sudo_list"]: return bot.reply_to(m, "⚠️ این کاربر از قبل سودو است.")
    d["sudo_list"].append(uid); save_data(d)
    bot.reply_to(m, f"✅ سودو {uid} افزوده شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "سلام" and is_sudo(m.from_user.id))
def sudo_greet(m): bot.reply_to(m, "👑 سلام سودوی عزیز، در خدمتتم!")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "افزودن مدیر")
def add_admin(m):
    if not is_sudo(m.from_user.id): return
    d = load_data(); gid = str(m.chat.id)
    uid = str(m.reply_to_message.from_user.id)
    d["admins"].setdefault(gid, [])
    if uid in d["admins"][gid]: return bot.reply_to(m, "⚠️ از قبل مدیر است.")
    d["admins"][gid].append(uid); save_data(d)
    bot.reply_to(m, f"✅ مدیر {uid} افزوده شد.")

# ================= 🚫 بن و اخطار =================
WARN_LIMIT = 3
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "اخطار")
def warn_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    d = load_data(); gid = str(m.chat.id); uid = str(m.reply_to_message.from_user.id)
    d["banned"].setdefault(gid, {})
    d["banned"][gid][uid] = d["banned"][gid].get(uid, 0) + 1
    warns = d["banned"][gid][uid]; save_data(d)
    if warns >= WARN_LIMIT:
        try:
            bot.ban_chat_member(m.chat.id, int(uid))
            bot.reply_to(m, f"🚫 کاربر {uid} به دلیل دریافت 3 اخطار بن شد.")
        except:
            bot.reply_to(m, "❗ خطا در بن کاربر.")
    else:
        bot.reply_to(m, f"⚠️ اخطار {warns}/3 به کاربر داده شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "بن")
def ban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    if is_sudo(uid): return bot.reply_to(m, "⚡ نمی‌توان سودو را بن کرد.")
    try:
        bot.ban_chat_member(m.chat.id, uid)
        bot.reply_to(m, f"🚫 کاربر {uid} بن شد.")
    except: bot.reply_to(m, "❗ خطا در بن.")

# ================= 🧹 پاکسازی =================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("حذف "))
def delete_n(m):
    try: n = int(cmd_text(m).split()[1])
    except: return bot.reply_to(m, "❗ فرمت درست: حذف 10")
    for i in range(1, n + 1):
        try: bot.delete_message(m.chat.id, m.message_id - i)
        except: continue
    bot.reply_to(m, f"🗑 {n} پیام پاک شد.")

# ================= 😂 جوک و 🔮 فال =================
@bot.message_handler(func=lambda m: cmd_text(m) == "جوک")
def send_joke(m):
    d = load_data(); jokes = d["jokes"]
    if not jokes: return bot.reply_to(m, "❗ جوکی ثبت نشده.")
    bot.reply_to(m, random.choice(jokes))

@bot.message_handler(func=lambda m: cmd_text(m) == "فال")
def send_fal(m):
    d = load_data(); falls = d["falls"]
    if not falls: return bot.reply_to(m, "❗ فالی ثبت نشده.")
    bot.reply_to(m, random.choice(falls))

# ================= 🚀 اجرای ربات =================
print("🤖 Bot is running...")
bot.infinity_polling(timeout=60, long_polling_timeout=30)
