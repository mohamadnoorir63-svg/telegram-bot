# -*- coding: utf-8 -*-
import os, json, random, logging
from datetime import datetime
import pytz, jdatetime
import telebot
from telebot import types

# ================= ⚙️ تنظیمات اولیه =================
TOKEN = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

DATA_FILE = "data.json"
LOG_FILE = "error.log"

logging.basicConfig(filename=LOG_FILE, level=logging.ERROR,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# ================= 🔒 قفل‌ها =================
LOCK_MAP = {
    "لینک": "link", "گروه": "group", "عکس": "photo", "ویدیو": "video",
    "استیکر": "sticker", "گیف": "gif", "فایل": "file",
    "موزیک": "music", "ویس": "voice", "فوروارد": "forward"
}

# ================= 📂 داده‌ها =================
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
    for k in base_data():
        if k not in data:
            data[k] = base_data()[k]
    save_data(data)
    return data

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def now_teh(): return datetime.now(pytz.timezone("Asia/Tehran"))
def shamsi_date(): return jdatetime.datetime.now().strftime("%A %d %B %Y")
def shamsi_time(): return jdatetime.datetime.now().strftime("%H:%M:%S")

def register_group(gid):
    data = load_data()
    gid = str(gid)
    data["welcome"].setdefault(gid, {"enabled": True, "type": "text", "content": None, "file_id": None})
    data["locks"].setdefault(gid, {k: False for k in LOCK_MAP.values()})
    if gid not in data["stats"]:
        data["stats"][gid] = {
            "date": str(datetime.now().date()),
            "users": {},
            "counts": {k:0 for k in ["msg","photo","video","voice","music","sticker","gif","fwd"]}
        }
    save_data(data)

# ================= ⚙️ ابزار =================
def cmd_text(m): return (getattr(m, "text", None) or "").strip()
def is_sudo(uid): d = load_data(); return str(uid) in [str(SUDO_ID)] + d.get("sudo_list", [])
def is_admin(chat_id, uid):
    d = load_data(); gid = str(chat_id)
    if is_sudo(uid): return True
    if str(uid) in d["admins"].get(gid, []): return True
    try:
        st = bot.get_chat_member(chat_id, uid).status
        return st in ("administrator", "creator")
    except: return False

# ================= 📜 دستورات کاربردی عمومی =================
@bot.message_handler(func=lambda m: cmd_text(m) == "آیدی")
def show_id(m):
    user = m.from_user
    bot.send_photo(
        m.chat.id,
        bot.get_user_profile_photos(user.id, limit=1).photos[0][-1].file_id if bot.get_user_profile_photos(user.id).total_count else None,
        caption=f"🪪 <b>نام:</b> {user.first_name}\n🆔 <b>آیدی:</b> <code>{user.id}</code>\n💬 <b>نام کاربری:</b> @{user.username if user.username else 'ندارد'}\n📅 <b>تاریخ:</b> {shamsi_date()}\n⏰ <b>ساعت:</b> {shamsi_time()}"
    )

@bot.message_handler(func=lambda m: cmd_text(m) == "ساعت")
def show_time(m):
    bot.reply_to(m, f"⏰ ساعت اکنون: {shamsi_time()}")

@bot.message_handler(func=lambda m: cmd_text(m) == "لینک گروه")
def get_group_link(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        link = bot.export_chat_invite_link(m.chat.id)
        bot.reply_to(m, f"🔗 لینک گروه:\n{link}")
    except:
        bot.reply_to(m, "⚠️ امکان دریافت لینک نیست (سطح دسترسی کافی نیست).")

@bot.message_handler(func=lambda m: cmd_text(m) == "لینک ربات")
def bot_link(m):
    uname = bot.get_me().username
    bot.reply_to(m, f"🤖 لینک ربات:\nhttps://t.me/{uname}")

# ================= 🎛️ پنل شیشه‌ای لوکس =================
def main_panel():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🔒 قفل‌ها", callback_data="locks"),
        types.InlineKeyboardButton("👋 خوشامد", callback_data="welcome"),
        types.InlineKeyboardButton("🚫 بن / اخطار", callback_data="ban"),
        types.InlineKeyboardButton("😂 جوک و فال", callback_data="fun"),
        types.InlineKeyboardButton("📊 آمار", callback_data="stats"),
        types.InlineKeyboardButton("🧹 پاکسازی", callback_data="clear"),
        types.InlineKeyboardButton("📢 ارسال", callback_data="broadcast"),
        types.InlineKeyboardButton("👥 مدیران", callback_data="admins"),
        types.InlineKeyboardButton("👑 سودوها", callback_data="sudos"),
        types.InlineKeyboardButton("ℹ️ راهنما", callback_data="help")
    )
    return kb

@bot.message_handler(commands=["panel", "پنل"])
def open_panel(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🧭 باز کردن پنل مدیریتی", callback_data="main"))
    bot.send_message(m.chat.id, "🎛️ برای باز کردن پنل مدیریتی کلیک کن 👇", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    data = call.data
    if data == "main":
        bot.edit_message_text("🎛️ <b>پنل مدیریتی فعال شد:</b>", call.message.chat.id, call.message.message_id, reply_markup=main_panel())

    elif data == "help":
        text = (
            "📘 <b>راهنمای سریع:</b>\n"
            "• آیدی — نمایش اطلاعات شما\n"
            "• ساعت — ساعت کنونی ایران\n"
            "• آمار — وضعیت فعالیت گروه\n"
            "• پنل — مدیریت قفل‌ها و خوشامد\n"
            "• فقط مدیران و سودوها دسترسی دارند ✅"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="main"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)# ================= 🔒 قفل‌ها =================
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

# ================= 🚧 اجرای قفل‌ها و آمار =================
@bot.message_handler(content_types=['text','photo','video','document','audio','voice','sticker','animation','video_note'])
def enforce(m):
    try:
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

        # ثبت آمار
        d = load_data()
        today = str(datetime.now().date())
        if d["stats"][gid]["date"] != today:
            d["stats"][gid]["date"] = today
            d["stats"][gid]["users"] = {}
            d["stats"][gid]["counts"] = {k:0 for k in d["stats"][gid]["counts"]}
        st = d["stats"][gid]
        uid = str(m.from_user.id)
        st["users"].setdefault(uid, 0)
        st["users"][uid] += 1
        if m.photo: st["counts"]["photo"] += 1
        elif m.video: st["counts"]["video"] += 1
        elif m.voice: st["counts"]["voice"] += 1
        elif m.audio: st["counts"]["music"] += 1
        elif m.sticker: st["counts"]["sticker"] += 1
        elif m.animation: st["counts"]["gif"] += 1
        elif m.forward_from or m.forward_from_chat: st["counts"]["fwd"] += 1
        else: st["counts"]["msg"] += 1
        save_data(d)
    except Exception as e:
        logging.error(f"enforce error: {e}")

# ================= 💬 خوشامد =================
@bot.message_handler(content_types=["new_chat_members"])
def welcome(m):
    register_group(m.chat.id)
    data = load_data(); gid = str(m.chat.id)
    s = data["welcome"].get(gid, {"enabled": True, "type": "text", "content": None, "file_id": None})
    if not s.get("enabled", True): return
    user = m.new_chat_members[0]
    name = user.first_name or "دوست جدید"
    t = shamsi_time()
    text = s.get("content") or f"سلام {name} 🌙\nبه گروه {m.chat.title} خوش اومدی 😎\n⏰ {t}"
    text = text.replace("{name}", name).replace("{time}", t)
    if s.get("file_id"): bot.send_photo(m.chat.id, s["file_id"], caption=text)
    else: bot.send_message(m.chat.id, text)

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "تنظیم خوشامد" and m.reply_to_message)
def set_welcome(m):
    data = load_data(); gid = str(m.chat.id)
    msg = m.reply_to_message
    if msg.photo:
        fid = msg.photo[-1].file_id
        caption = msg.caption or " "
        data["welcome"][gid] = {"enabled": True, "type": "photo", "content": caption, "file_id": fid}
    elif msg.text:
        data["welcome"][gid] = {"enabled": True, "type": "text", "content": msg.text, "file_id": None}
    save_data(data)
    bot.reply_to(m, "✅ پیام خوشامد جدید تنظیم شد.")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) in ["خوشامد روشن", "خوشامد خاموش"])
def toggle_welcome(m):
    data = load_data(); gid = str(m.chat.id)
    en = cmd_text(m) == "خوشامد روشن"
    data["welcome"].setdefault(gid, {"enabled": True})
    data["welcome"][gid]["enabled"] = en
    save_data(data)
    bot.reply_to(m, "✅ خوشامد روشن شد" if en else "🚫 خوشامد خاموش شد")

# ================= 😂 جوک و 🔮 فال =================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "ثبت جوک" and m.reply_to_message)
def add_joke(m):
    data = load_data()
    data["jokes"].append(m.reply_to_message.text)
    save_data(data)
    bot.reply_to(m, "😂 جوک ذخیره شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "جوک")
def send_joke(m):
    data = load_data(); jokes = data.get("jokes", [])
    if not jokes: return bot.reply_to(m, "❗ جوکی ثبت نشده.")
    bot.reply_to(m, random.choice(jokes))

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "ثبت فال" and m.reply_to_message)
def add_fal(m):
    data = load_data()
    data["falls"].append(m.reply_to_message.text)
    save_data(data)
    bot.reply_to(m, "🔮 فال ذخیره شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "فال")
def send_fal(m):
    data = load_data(); falls = data.get("falls", [])
    if not falls: return bot.reply_to(m, "❗ فالی ثبت نشده.")
    bot.reply_to(m, random.choice(falls))

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "لیست جوک‌ها")
def list_jokes(m):
    data = load_data(); jokes = data.get("jokes", [])
    if not jokes: return bot.reply_to(m, "❗ جوکی ثبت نشده.")
    txt = "\n".join([f"{i+1}. {t}" for i, t in enumerate(jokes)])
    bot.reply_to(m, "📜 لیست جوک‌ها:\n" + txt)

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "لیست فال‌ها")
def list_fals(m):
    data = load_data(); falls = data.get("falls", [])
    if not falls: return bot.reply_to(m, "❗ فالی ثبت نشده.")
    txt = "\n".join([f"{i+1}. {t}" for i, t in enumerate(falls)])
    bot.reply_to(m, "📜 لیست فال‌ها:\n" + txt)

# ================= 📢 ارسال همگانی (فقط سودو) =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ارسال" and m.reply_to_message)
def broadcast(m):
    data = load_data()
    users = list(set(data.get("users", [])))
    groups = [int(g) for g in data.get("welcome", {}).keys()]
    msg = m.reply_to_message; total = 0
    for uid in users + groups:
        try:
            if msg.text: bot.send_message(uid, msg.text)
            elif msg.photo: bot.send_photo(uid, msg.photo[-1].file_id, caption=msg.caption or "")
            total += 1
        except: continue
    bot.reply_to(m, f"📢 پیام به {total} کاربر ارسال شد.")

# ================= 👑 پاسخ سودو =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).lower() in ["سلام","ربات","bot"])
def sudo_reply(m):
    bot.reply_to(m, f"سلام 👑 {m.from_user.first_name}!\nدر خدمتتم سودوی عزیز 🤖")

# ================= 🚀 اجرای ربات =================
if __name__ == "__main__":
    print("🤖 ربات مدیریتی V13.8 Persian Pro – Lux Panel (Full Pack) فعال شد!")
    bot.infinity_polling(timeout=60, long_polling_timeout=30)
