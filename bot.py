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
    data["stats"].setdefault(gid, {"msg":0,"photo":0,"video":0,"voice":0,"music":0,"sticker":0,"gif":0})
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
        bot.send_message(m.chat.id, "🔒 گروه بسته شد." if en else "🔓 گروه باز شد.")
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
    if locks.get("group"):
        try: bot.delete_message(m.chat.id, m.message_id)
        except: pass
        return
    if locks.get("link") and any(x in txt for x in ["http://","https://","t.me","telegram.me"]):
        try: bot.delete_message(m.chat.id, m.message_id)
        except: pass
        return
    if locks.get("photo") and m.photo: bot.delete_message(m.chat.id, m.message_id)
    if locks.get("video") and m.video: bot.delete_message(m.chat.id, m.message_id)
    if locks.get("sticker") and m.sticker: bot.delete_message(m.chat.id, m.message_id)
    if locks.get("gif") and m.animation: bot.delete_message(m.chat.id, m.message_id)
    if locks.get("file") and m.document: bot.delete_message(m.chat.id, m.message_id)
    if locks.get("music") and m.audio: bot.delete_message(m.chat.id, m.message_id)
    if locks.get("voice") and m.voice: bot.delete_message(m.chat.id, m.message_id)
    if locks.get("forward") and (m.forward_from or m.forward_from_chat): bot.delete_message(m.chat.id, m.message_id)

# ================= 💬 عمومی =================
@bot.message_handler(func=lambda m: cmd_text(m) in ["آیدی","ایدی"])
def cmd_id(m):
    try:
        photos = bot.get_user_profile_photos(m.from_user.id, limit=1)
        caption = (
            f"🆔 شما: <code>{m.from_user.id}</code>\n"
            f"🆔 گروه: <code>{m.chat.id}</code>\n"
            f"📅 {shamsi_date()}"
        )
        if photos.total_count > 0:
            bot.send_photo(m.chat.id, photos.photos[0][-1].file_id, caption=caption)
        else:
            bot.reply_to(m, caption)
    except:
        bot.reply_to(m, caption)

@bot.message_handler(func=lambda m: cmd_text(m) == "ساعت")
def cmd_time(m):
    bot.reply_to(m, f"⏰ {shamsi_date()}")

@bot.message_handler(func=lambda m: cmd_text(m) == "لینک گروه")
def group_link(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        invite = bot.export_chat_invite_link(m.chat.id)
        bot.reply_to(m, f"🔗 لینک گروه:\n{invite}")
    except:
        bot.reply_to(m, "❗ خطا در دریافت لینک.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لینک ربات")
def bot_link(m):
    bot.reply_to(m, f"🤖 لینک ربات:\nhttps://t.me/{bot.get_me().username}")

# ================= 📢 ارسال همگانی =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ارسال" and m.reply_to_message)
def broadcast(m):
    data = load_data()
    users = list(set(data.get("users", [])))
    groups = [int(g) for g in data.get("welcome", {}).keys()]
    total = 0
    msg = m.reply_to_message
    for uid in users + groups:
        try:
            if msg.text: bot.send_message(uid, msg.text)
            elif msg.photo: bot.send_photo(uid, msg.photo[-1].file_id, caption=msg.caption or "")
            total += 1
        except: continue
    bot.reply_to(m, f"📢 پیام به {total} کاربر ارسال شد.")

# ================= 👑 پاسخ مخصوص سودو =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id))
def sudo_chat(m):
    txt = cmd_text(m)
    replies = [
        "👑 در خدمتتم سودوی عزیز!",
        "💬 بگو قربان!",
        "🌟 بله فرمانده!",
        "😎 همیشه آماده‌ام!"
    ]
    if any(x in txt for x in ["سلام","ربات","هستی","چطوری"]):
        bot.reply_to(m, random.choice(replies))

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

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ثبت جوک" and m.reply_to_message)
def add_joke(m):
    d = load_data(); d["jokes"].append(m.reply_to_message.text)
    save_data(d); bot.reply_to(m, "😂 جوک ذخیره شد.")

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ثبت فال" and m.reply_to_message)
def add_fal(m):
    d = load_data(); d["falls"].append(m.reply_to_message.text)
    save_data(d); bot.reply_to(m, "🔮 فال ذخیره شد.")

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "لیست جوک‌ها")
def list_jokes(m):
    d = load_data(); jokes = d["jokes"]
    if not jokes: return bot.reply_to(m, "❗ جوکی ثبت نشده.")
    msg = "\n".join([f"{i+1}. {t}" for i, t in enumerate(jokes)])
    bot.reply_to(m, f"😂 لیست جوک‌ها:\n{msg}")

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "لیست فال‌ها")
def list_fals(m):
    d = load_data(); falls = d["falls"]
    if not falls: return bot.reply_to(m, "❗ فالی ثبت نشده.")
    msg = "\n".join([f"{i+1}. {t}" for i, t in enumerate(falls)])
    bot.reply_to(m, f"🔮 لیست فال‌ها:\n{msg}")

# ================= 🚀 اجرای ربات =================
print("🤖 Bot is running...")
bot.infinity_polling(timeout=60, long_polling_timeout=30)
