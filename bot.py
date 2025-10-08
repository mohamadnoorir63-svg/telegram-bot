# -*- coding: utf-8 -*-
import os, json, random
from datetime import datetime
import pytz, jdatetime
import telebot
from telebot import types

# ================== ⚙️ تنظیمات ==================
TOKEN   = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
DATA_FILE = "data.json"

# ================== 📂 فایل دیتا ==================
def base_data():
    return {
        "welcome": {},
        "locks": {},
        "admins": {},
        "sudo_list": [],
        "banned": {},
        "muted": {},
        "users": [],
        "jokes": [],
        "falls": []
    }

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(base_data())
        return base_data()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
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
    data["locks"].setdefault(gid, {k: False for k in ["link","group","photo","video","sticker","gif","file","music","voice","forward"]})
    save_data(data)

# ================== 🧩 کمکی ==================
def is_sudo(uid):
    data = load_data()
    return str(uid) in [str(SUDO_ID)] + data.get("sudo_list", [])

def is_admin(chat_id, uid):
    data = load_data()
    gid = str(chat_id)
    if is_sudo(uid): return True
    if str(uid) in data["admins"].get(gid, []): return True
    try:
        st = bot.get_chat_member(chat_id, uid).status
        return st in ("administrator", "creator")
    except:
        return False

def cmd_text(m): return (getattr(m, "text", None) or "").strip()
def now_teh(): return datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
def now_shamsi(): return jdatetime.datetime.now().strftime("%H:%M (%A %d %B %Y)")

# ================== پاسخ به سودو ==================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "سلام")
def sudo_greet(m):
    bot.reply_to(m, "👑 سلام سودوی عزیز! در خدمتتم 🙌")

# ================== ⚙️ مدیریت سودو ==================
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "افزودن سودو")
def add_sudo(m):
    if m.from_user.id != SUDO_ID:
        return
    data = load_data()
    uid = str(m.reply_to_message.from_user.id)
    if uid in data["sudo_list"]:
        return bot.reply_to(m, "⚠️ این کاربر از قبل سودو است.")
    data["sudo_list"].append(uid)
    save_data(data)
    bot.reply_to(m, f"✅ کاربر {uid} به لیست سودوها اضافه شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف سودو")
def remove_sudo(m):
    if m.from_user.id != SUDO_ID:
        return
    data = load_data()
    uid = str(m.reply_to_message.from_user.id)
    if uid not in data["sudo_list"]:
        return bot.reply_to(m, "❌ این کاربر در لیست سودوها نیست.")
    data["sudo_list"].remove(uid)
    save_data(data)
    bot.reply_to(m, f"🗑 سودو {uid} حذف شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست سودوها")
def list_sudo(m):
    if not is_sudo(m.from_user.id): return
    data = load_data()
    sudo_list = data.get("sudo_list", [])
    if not sudo_list: return bot.reply_to(m, "❗ هیچ سودویی ثبت نشده.")
    bot.reply_to(m, "👑 لیست سودوها:\n" + "\n".join(sudo_list))

# ================== 👑 مدیران ==================
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "افزودن مدیر")
def add_admin(m):
    if not is_sudo(m.from_user.id): return
    data = load_data(); gid = str(m.chat.id)
    uid = str(m.reply_to_message.from_user.id)
    data["admins"].setdefault(gid, [])
    if uid not in data["admins"][gid]:
        data["admins"][gid].append(uid)
        save_data(data)
        bot.reply_to(m, f"✅ {uid} به مدیران افزوده شد.")
    else:
        bot.reply_to(m, "⚠️ این کاربر از قبل مدیر است.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست مدیران")
def list_admins(m):
    data = load_data(); gid = str(m.chat.id)
    lst = data["admins"].get(gid, [])
    if not lst:
        return bot.reply_to(m, "❗ هیچ مدیری ثبت نشده.")
    bot.reply_to(m, "👑 لیست مدیران:\n" + "\n".join(lst))

# ================== 💬 عمومی ==================
@bot.message_handler(func=lambda m: cmd_text(m) in ["آیدی","ایدی"])
def cmd_id(m):
    bot.reply_to(m, f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 گروه: <code>{m.chat.id}</code>")

@bot.message_handler(func=lambda m: cmd_text(m) == "ساعت")
def cmd_time(m):
    bot.reply_to(m, f"⏰ تهران: {now_teh()}\n📅 شمسی: {now_shamsi()}")

@bot.message_handler(func=lambda m: cmd_text(m) == "آمار")
def cmd_stats(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try: count = bot.get_chat_member_count(m.chat.id)
    except: count = "نامشخص"
    bot.reply_to(m, f"📊 اعضای گروه: {count}")

# ================== 🎉 خوشامد ==================
@bot.message_handler(content_types=["new_chat_members"])
def welcome(m):
    register_group(m.chat.id)
    data = load_data(); gid = str(m.chat.id)
    s = data["welcome"].get(gid, {"enabled": True})
    if not s.get("enabled", True): return
    name = m.new_chat_members[0].first_name or "دوست جدید"
    t = now_shamsi()
    text = s.get("content") or f"سلام {name} 🌙\nبه گروه {m.chat.title} خوش اومدی 😎\n⏰ {t}"
    if s.get("type") == "photo" and s.get("file_id"):
        bot.send_photo(m.chat.id, s["file_id"], caption=text)
    else:
        bot.send_message(m.chat.id, text)

@bot.message_handler(func=lambda m: cmd_text(m) in ["خوشامد روشن","خوشامد خاموش"])
def toggle_welcome(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    data = load_data(); gid = str(m.chat.id)
    en = cmd_text(m) == "خوشامد روشن"
    data["welcome"].setdefault(gid, {})
    data["welcome"][gid]["enabled"] = en
    save_data(data)
    bot.reply_to(m, "✅ خوشامد روشن شد" if en else "🚫 خوشامد خاموش شد")

@bot.message_handler(func=lambda m: cmd_text(m) == "تنظیم خوشامد" and m.reply_to_message)
def set_welcome(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    data = load_data(); gid = str(m.chat.id)
    if m.reply_to_message.photo:
        data["welcome"][gid] = {"enabled": True, "type": "photo", "file_id": m.reply_to_message.photo[-1].file_id, "content": m.reply_to_message.caption}
    else:
        txt = (m.reply_to_message.text or "").strip()
        data["welcome"][gid] = {"enabled": True, "type": "text", "content": txt}
    save_data(data)
    bot.reply_to(m, "📝 پیام خوشامد تنظیم شد.")

# ================== 🔒 قفل‌ها ==================
LOCK_MAP = {
    "لینک": "link","گروه": "group","عکس": "photo","ویدیو": "video",
    "استیکر": "sticker","گیف": "gif","فایل": "file",
    "موزیک": "music","ویس": "voice","فوروارد": "forward"
}

@bot.message_handler(func=lambda m: cmd_text(m).startswith("قفل ") or cmd_text(m).startswith("بازکردن "))
def toggle_lock(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    data = load_data(); gid = str(m.chat.id)
    part = cmd_text(m).split(" ")
    if len(part) < 2: return
    key_fa = part[1]
    lock_type = LOCK_MAP.get(key_fa)
    if not lock_type: return bot.reply_to(m, "❌ نوع قفل نامعتبر است.")
    en = cmd_text(m).startswith("قفل ")
    data["locks"].setdefault(gid, {k: False for k in LOCK_MAP.values()})
    if data["locks"][gid][lock_type] == en:
        return bot.reply_to(m, "⚠️ این مورد از قبل همین حالت بود.")
    data["locks"][gid][lock_type] = en
    save_data(data)
    if key_fa == "گروه":
        msg = "🔒 گروه به دستور مدیر بسته شد." if en else "🔓 گروه توسط مدیر باز شد."
        bot.send_message(m.chat.id, msg)
    bot.reply_to(m, f"🔒 قفل {key_fa} فعال شد" if en else f"🔓 قفل {key_fa} غیرفعال شد")

# ================== 🚫 بن / سکوت با اخطار ==================
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "بن")
def ban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    if is_sudo(uid): return bot.reply_to(m, "⚡ نمی‌توان سودو را بن کرد.")
    try:
        bot.send_message(m.chat.id, f"🚨 کاربر <a href='tg://user?id={uid}'>بن شد</a> به علت نقض قوانین.", parse_mode="HTML")
        try: bot.send_message(uid, "🚨 شما به علت نقض قوانین از گروه بن شدید.")
        except: pass
        bot.ban_chat_member(m.chat.id, uid)
        bot.reply_to(m, f"🚫 کاربر {uid} بن شد.")
    except:
        bot.reply_to(m, "❗ خطا در انجام عملیات بن.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف بن")
def unban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    try:
        bot.unban_chat_member(m.chat.id, uid, only_if_banned=True)
        bot.reply_to(m, "✅ بن حذف شد.")
    except:
        bot.reply_to(m, "❗ خطا در حذف بن.")

# ================== 😂 جوک و 🔮 فال ==================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ثبت جوک" and m.reply_to_message)
def add_joke(m):
    data = load_data(); data["jokes"].append(m.reply_to_message.text)
    save_data(data); bot.reply_to(m, "😂 جوک ذخیره شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "جوک")
def send_joke(m):
    data = load_data(); jokes = data["jokes"]
    if not jokes: return bot.reply_to(m, "❗ جوکی ثبت نشده.")
    bot.reply_to(m, random.choice(jokes))

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست جوک‌ها")
def list_jokes(m):
    data = load_data(); jokes = data["jokes"]
    if not jokes: return bot.reply_to(m, "❗ هیچ جوکی ثبت نشده.")
    txt = "\n".join([f"{i+1}. {j}" for i,j in enumerate(jokes)])
    bot.reply_to(m, "😂 لیست جوک‌ها:\n" + txt)

@bot.message_handler(func=lambda m: cmd_text(m) == "ثبت فال" and m.reply_to_message)
def add_fal(m):
    if not is_sudo(m.from_user.id): return
    data = load_data(); data["falls"].append(m.reply_to_message.text)
    save_data(data); bot.reply_to(m, "🔮 فال ذخیره شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "فال")
def send_fal(m):
    data = load_data(); falls = data["falls"]
    if not falls: return bot.reply_to(m, "❗ فالی ثبت نشده.")
    bot.reply_to(m, random.choice(falls))

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست فال‌ها")
def list_fals(m):
    data = load_data(); falls = data["falls"]
    if not falls: return bot.reply_to(m, "❗ فالی ثبت نشده.")
    txt = "\n".join([f"{i+1}. {f}" for i,f in enumerate(falls)])
    bot.reply_to(m, "🔮 لیست فال‌ها:\n" + txt)

# ================== 📢 ارسال همگانی ==================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ارسال" and m.reply_to_message)
def broadcast(m):
    data = load_data()
    users = list(set(data["users"]))
    groups = [int(g) for g in data["welcome"].keys()]
    total = 0; msg = m.reply_to_message
    for uid in users + groups:
        try:
            if msg.text: bot.send_message(uid, msg.text)
            elif msg.photo: bot.send_photo(uid, msg.photo[-1].file_id, caption=msg.caption or "")
            total += 1
        except: continue
    bot.reply_to(m, f"📢 پیام به {total} کاربر ارسال شد.")

# ================== 🧹 پاکسازی ==================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("حذف "))
def delete_msgs(m):
    try: n = int(cmd_text(m).split()[1])
    except: return bot.reply_to(m, "❗ فرمت درست: حذف 10")
    count = 0
    for i in range(1, n+1):
        try: bot.delete_message(m.chat.id, m.message_id - i); count += 1
        except: continue
    bot.reply_to(m, f"🧹 {count} پیام حذف شد.")

# ================== 🚀 اجرای ربات ==================
print("🤖 Bot is running...")
bot.infinity_polling(timeout=60, long_polling_timeout=30)
