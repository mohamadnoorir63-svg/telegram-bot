# -*- coding: utf-8 -*-
import os, json, random
from datetime import datetime
import pytz, jdatetime
import telebot
from telebot import types

# ================= ⚙️ تنظیمات =================
TOKEN = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
DATA_FILE = "data.json"

# ================= 📂 داده =================
def base_data():
    return {
        "welcome": {},
        "locks": {},
        "admins": {},
        "sudo_list": [],
        "banned": {},
        "muted": {},
        "warns": {},
        "jokes": [],
        "falls": [],
        "users": [],
        "stats": {}
    }

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(base_data())
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
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
    data["stats"].setdefault(gid, {
        "msg":0,"photo":0,"video":0,"voice":0,"music":0,"sticker":0,"gif":0,"fwd":0
    })
    save_data(data)

# ================= 🧩 ابزارها =================
def cmd_text(m): return (getattr(m, "text", None) or "").strip()
def now_teh(): return datetime.now(pytz.timezone("Asia/Tehran"))
def shamsi_date(): return jdatetime.datetime.now().strftime("%A %d %B %Y - %H:%M:%S")

def is_sudo(uid):
    d = load_data()
    return str(uid) in [str(SUDO_ID)] + d.get("sudo_list", [])

def is_admin(chat_id, uid):
    d = load_data()
    gid = str(chat_id)
    if is_sudo(uid): return True
    if str(uid) in d["admins"].get(gid, []): return True
    try:
        st = bot.get_chat_member(chat_id, uid).status
        return st in ("administrator", "creator")
    except: return False

# ================= 🔒 قفل‌ها =================
LOCK_MAP = {
    "لینک": "link", "گروه": "group", "عکس": "photo", "ویدیو": "video",
    "استیکر": "sticker", "گیف": "gif", "فایل": "file",
    "موزیک": "music", "ویس": "voice", "فوروارد": "forward"
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
        msg = "⚠️ این مورد از قبل قفل بود." if en else "⚠️ این مورد از قبل باز بود."
        return bot.reply_to(m, msg)
    data["locks"][gid][lock_type] = en
    save_data(data)
    if lock_type == "group":
        bot.send_message(m.chat.id, "🔒 گروه به دستور مدیر بسته شد." if en else "🔓 گروه توسط مدیر باز شد.")
    else:
        bot.reply_to(m, f"🔒 قفل {key_fa} فعال شد" if en else f"🔓 قفل {key_fa} غیرفعال شد")

# ================= 🚧 اجرای قفل‌ها =================
@bot.message_handler(content_types=['text','photo','video','document','audio','voice','sticker','animation','video_note'])
def enforce(m):
    register_group(m.chat.id)
    if is_admin(m.chat.id, m.from_user.id): return
    data = load_data(); gid = str(m.chat.id)
    locks = data["locks"].get(gid, {})
    txt = (m.text or "") + " " + (getattr(m, "caption", "") or "")
    if locks.get("group"): return bot.delete_message(m.chat.id, m.message_id)
    if locks.get("link") and any(x in txt for x in ["http://","https://","t.me","telegram.me"]):
        return bot.delete_message(m.chat.id, m.message_id)
    if locks.get("photo") and m.photo: bot.delete_message(m.chat.id, m.message_id)
    if locks.get("video") and m.video: bot.delete_message(m.chat.id, m.message_id)
    if locks.get("sticker") and m.sticker: bot.delete_message(m.chat.id, m.message_id)
    if locks.get("gif") and m.animation: bot.delete_message(m.chat.id, m.message_id)
    if locks.get("file") and m.document: bot.delete_message(m.chat.id, m.message_id)
    if locks.get("music") and m.audio: bot.delete_message(m.chat.id, m.message_id)
    if locks.get("voice") and m.voice: bot.delete_message(m.chat.id, m.message_id)
    if locks.get("forward") and (m.forward_from or m.forward_from_chat): bot.delete_message(m.chat.id, m.message_id)

# ================= 🎉 خوشامد =================
@bot.message_handler(content_types=["new_chat_members"])
def welcome(m):
    register_group(m.chat.id)
    data = load_data(); gid = str(m.chat.id)
    s = data["welcome"][gid]
    if not s.get("enabled", True): return
    name = m.new_chat_members[0].first_name or "دوست جدید"
    t = shamsi_date()
    txt = s["content"] or f"سلام {name} 🌸 خوش اومدی به گروه {m.chat.title} 💬"
    txt = txt.replace("{name}", name).replace("{time}", t)
    if s.get("file_id"):
        bot.send_photo(m.chat.id, s["file_id"], caption=txt)
    else:
        bot.send_message(m.chat.id, txt)

@bot.message_handler(func=lambda m: cmd_text(m) == "تنظیم خوشامد" and m.reply_to_message)
def set_welcome(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    d = load_data(); gid = str(m.chat.id)
    msg = m.reply_to_message
    if msg.photo:
        d["welcome"][gid] = {"enabled": True, "type": "photo", "content": msg.caption or None, "file_id": msg.photo[-1].file_id}
    else:
        d["welcome"][gid] = {"enabled": True, "type": "text", "content": msg.text or None, "file_id": None}
    save_data(d)
    bot.reply_to(m, "✅ پیام خوشامد تنظیم شد.")

# ================= 🚫 بن، سکوت، اخطار =================
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "بن")
def ban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    if is_sudo(uid): return bot.reply_to(m, "⚡ نمی‌توان سودو را بن کرد.")
    try:
        bot.ban_chat_member(m.chat.id, uid)
        bot.reply_to(m, f"🚫 کاربر {uid} بن شد.")
    except: bot.reply_to(m, "❗ خطا در بن کاربر.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "اخطار")
def warn_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = str(m.reply_to_message.from_user.id)
    d = load_data(); gid = str(m.chat.id)
    d["warns"].setdefault(gid, {}).setdefault(uid, 0)
    d["warns"][gid][uid] += 1
    save_data(d)
    if d["warns"][gid][uid] >= 3:
        try:
            bot.ban_chat_member(m.chat.id, int(uid))
            bot.reply_to(m, f"🚫 کاربر {uid} پس از 3 اخطار بن شد.")
            d["warns"][gid][uid] = 0
            save_data(d)
        except: pass
    else:
        bot.reply_to(m, f"⚠️ اخطار {d['warns'][gid][uid]} برای کاربر {uid}")

# ================= 🧹 پاکسازی =================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "پاکسازی")
def clear(m):
    for i in range(1, 101):
        try: bot.delete_message(m.chat.id, m.message_id - i)
        except: continue
    bot.reply_to(m, "🧹 پیام‌ها پاک شدند.")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("حذف "))
def delete_n(m):
    try: n = int(cmd_text(m).split()[1])
    except: return bot.reply_to(m, "❗ فرمت درست: حذف 10")
    for i in range(1, n + 1):
        try: bot.delete_message(m.chat.id, m.message_id - i)
        except: continue
    bot.reply_to(m, f"🗑 {n} پیام پاک شد.")

# ================= 👑 مدیران و سودو =================
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "افزودن مدیر")
def add_admin(m):
    if not is_sudo(m.from_user.id): return
    d = load_data(); gid = str(m.chat.id)
    uid = str(m.reply_to_message.from_user.id)
    d["admins"].setdefault(gid, [])
    if uid not in d["admins"][gid]:
        d["admins"][gid].append(uid)
        save_data(d)
        bot.reply_to(m, f"✅ {uid} به لیست مدیران افزوده شد.")
    else: bot.reply_to(m, "⚠️ این کاربر از قبل مدیر است.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست مدیران")
def list_admins(m):
    d = load_data(); gid = str(m.chat.id)
    lst = d["admins"].get(gid, [])
    if not lst: return bot.reply_to(m, "❗ مدیری ثبت نشده.")
    bot.reply_to(m, "👑 مدیران:\n" + "\n".join([f"• {i}" for i in lst]))

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "افزودن سودو")
def add_sudo(m):
    if m.from_user.id != SUDO_ID: return
    d = load_data(); uid = str(m.reply_to_message.from_user.id)
    if uid in d["sudo_list"]: return bot.reply_to(m, "⚠️ این کاربر سودو است.")
    d["sudo_list"].append(uid); save_data(d)
    bot.reply_to(m, f"✅ سودو {uid} افزوده شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست سودوها")
def list_sudo(m):
    if not is_sudo(m.from_user.id): return
    d = load_data(); lst = d["sudo_list"]
    if not lst: return bot.reply_to(m, "❗ سودوی اضافی ثبت نشده.")
    bot.reply_to(m, "👑 لیست سودوها:\n" + "\n".join(lst))

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

# ================= 📢 ارسال همگانی =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ارسال" and m.reply_to_message)
def broadcast(m):
    d = load_data(); msg = m.reply_to_message
    targets = list(set(d["users"])) + [int(g) for g in d["welcome"]]
    total = 0
    for uid in targets:
        try:
            if msg.text: bot.send_message(uid, msg.text)
            elif msg.photo: bot.send_photo(uid, msg.photo[-1].file_id, caption=msg.caption or "")
            total += 1
        except: continue
    bot.reply_to(m, f"📢 پیام به {total} کاربر ارسال شد.")

# ================= 👑 پاسخ سودو =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id))
def sudo_chat(m):
    if any(x in cmd_text(m) for x in ["سلام","ربات","چطوری"]):
        bot.reply_to(m, random.choice(["👑 سلام قربان!","💬 در خدمت شما هستم","⚡ بله قربان!"]))

# ================= 🚀 اجرای ربات =================
print("🤖 Bot is running...")
bot.infinity_polling(timeout=60, long_polling_timeout=30)
