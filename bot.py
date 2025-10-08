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

# ================= 🕒 زمان و تاریخ =================
def now_teh(): return datetime.now(pytz.timezone("Asia/Tehran"))
def shamsi_date(): return jdatetime.datetime.now().strftime("%A %d %B %Y")
def shamsi_time(): return jdatetime.datetime.now().strftime("%H:%M:%S")

# ================= 🧩 ثبت گروه =================
def register_group(gid):
    data = load_data()
    gid = str(gid)
    data["welcome"].setdefault(gid, {"enabled": True, "type": "text", "content": None, "file_id": None})
    data["locks"].setdefault(gid, {k: False for k in LOCK_MAP.values()})
    if gid not in data["stats"]:
        data["stats"][gid] = {
            "date": str(datetime.now().date()),
            "users": {},
            "counts": {k: 0 for k in ["msg", "photo", "video", "voice", "music", "sticker", "gif", "fwd"]}
        }
    save_data(data)

# ================= 🛠 ابزار =================
def cmd_text(m): return (getattr(m, "text", None) or "").strip()

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
    except:
        return False

# ================= 🔒 قفل‌ها =================
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
        msg = "🔒 گروه به دستور مدیر بسته شد 🚫" if en else "🔓 گروه باز شد ✅"
        bot.send_message(m.chat.id, msg)
    else:
        bot.reply_to(m, f"{'🔒' if en else '🔓'} قفل {key_fa} {'فعال' if en else 'غیرفعال'} شد ✅")

# ================= 🚫 اجرای قفل‌ها =================
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
            bot.delete_message(m.chat.id, m.message_id)
            return bot.send_message(m.chat.id, "🚫 ارسال لینک ممنوع است.")
        if locks.get("photo") and m.photo:
            bot.delete_message(m.chat.id, m.message_id)
            return bot.send_message(m.chat.id, "🖼 ارسال عکس ممنوع است.")
        if locks.get("video") and m.video:
            bot.delete_message(m.chat.id, m.message_id)
            return bot.send_message(m.chat.id, "🎬 ارسال ویدیو مجاز نیست.")
        if locks.get("sticker") and m.sticker:
            bot.delete_message(m.chat.id, m.message_id)
            return bot.send_message(m.chat.id, "😜 ارسال استیکر ممنوع است.")
        if locks.get("gif") and m.animation:
            bot.delete_message(m.chat.id, m.message_id)
            return bot.send_message(m.chat.id, "🎞 ارسال گیف مجاز نیست.")
        if locks.get("file") and m.document:
            bot.delete_message(m.chat.id, m.message_id)
            return bot.send_message(m.chat.id, "📁 ارسال فایل ممنوع است.")
        if locks.get("music") and m.audio:
            bot.delete_message(m.chat.id, m.message_id)
            return bot.send_message(m.chat.id, "🎵 ارسال آهنگ ممنوع است.")
        if locks.get("voice") and m.voice:
            bot.delete_message(m.chat.id, m.message_id)
            return bot.send_message(m.chat.id, "🎙 ارسال ویس مجاز نیست.")
        if locks.get("forward") and (m.forward_from or m.forward_from_chat):
            bot.delete_message(m.chat.id, m.message_id)
            return bot.send_message(m.chat.id, "⚠️ فوروارد پیام در این گروه بسته است.")
    except Exception as e:
        logging.error(f"enforce error: {e}")

# ================= 👋 خوشامد =================
@bot.message_handler(content_types=["new_chat_members"])
def welcome(m):
    register_group(m.chat.id)
    data = load_data(); gid = str(m.chat.id)
    s = data["welcome"].get(gid, {"enabled": True, "type": "text", "content": None, "file_id": None})
    if not s.get("enabled", True): return
    user = m.new_chat_members[0]
    name = user.first_name or "دوست جدید"
    t = shamsi_time()
    text = s.get("content") or f"سلام {name} 🌹\nبه گروه {m.chat.title} خوش اومدی 🌸\n⏰ {t}"
    text = text.replace("{name}", name).replace("{time}", t)
    if s.get("file_id"):
        bot.send_photo(m.chat.id, s["file_id"], caption=text)
    else:
        bot.send_message(m.chat.id, text)

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "تنظیم خوشامد" and m.reply_to_message)
def set_welcome(m):
    data = load_data(); gid = str(m.chat.id)
    msg = m.reply_to_message
    if msg.photo:
        fid = msg.photo[-1].file_id
        caption = msg.caption or ""
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
    bot.reply_to(m, "🌕 خوشامد فعال شد ✅" if en else "🌑 خوشامد غیرفعال شد 🚫")# ================= 🎛️ پنل شیشه‌ای لوکس =================
def main_panel():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🔒 قفل‌ها", callback_data="locks"),
        types.InlineKeyboardButton("👋 خوشامد", callback_data="welcome"),
        types.InlineKeyboardButton("🚫 محدودیت‌ها", callback_data="ban"),
        types.InlineKeyboardButton("😂 جوک و فال", callback_data="fun"),
        types.InlineKeyboardButton("📊 آمار", callback_data="stats"),
        types.InlineKeyboardButton("🧹 پاکسازی", callback_data="clear"),
        types.InlineKeyboardButton("👥 مدیران", callback_data="admins"),
        types.InlineKeyboardButton("👑 سودوها", callback_data="sudos"),
        types.InlineKeyboardButton("ℹ️ راهنما", callback_data="help"),
        types.InlineKeyboardButton("🔙 بستن پنل", callback_data="close")
    )
    return kb

@bot.message_handler(commands=["panel", "پنل"])
def open_panel(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    bot.send_message(
        m.chat.id,
        "🎛️ <b>پنل مدیریتی لوکس فعال شد!</b>\nبرای مدیریت از دکمه‌های زیر استفاده کن 👇",
        reply_markup=main_panel()
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    data = call.data
    if data == "close":
        bot.delete_message(call.message.chat.id, call.message.message_id)
    elif data == "help":
        txt = (
            "📘 <b>راهنمای سریع دستورات:</b>\n"
            "• آیدی — نمایش اطلاعات شما\n"
            "• ساعت — زمان کنونی ایران\n"
            "• آمار — گزارش فعالیت روزانه گروه\n"
            "• ثبت جوک / فال — ذخیره آیتم جدید\n"
            "• لیست جوک‌ها / فال‌ها — مشاهده همه\n"
            "• قفل (مثلاً عکس) / بازکردن (عکس)\n"
            "• بن / سکوت / اخطار + لیست\n"
            "• پاکسازی ۵۰ — حذف ۵۰ پیام آخر\n"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 برگشت", callback_data="main"))
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, reply_markup=kb)
    elif data == "main":
        bot.edit_message_text("🎛️ منوی اصلی مدیریت:", call.message.chat.id, call.message.message_id, reply_markup=main_panel())

# ================= 🚫 بن، سکوت و اخطار =================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("بن ") and m.reply_to_message)
def ban_user(m):
    data = load_data(); gid = str(m.chat.id)
    uid = str(m.reply_to_message.from_user.id)
    data["banned"].setdefault(gid, [])
    if uid not in data["banned"][gid]:
        data["banned"][gid].append(uid)
        bot.ban_chat_member(m.chat.id, int(uid))
        bot.reply_to(m, f"🚫 کاربر <b>{m.reply_to_message.from_user.first_name}</b> بن شد.")
    save_data(data)

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("سکوت ") and m.reply_to_message)
def mute_user(m):
    data = load_data(); gid = str(m.chat.id)
    uid = str(m.reply_to_message.from_user.id)
    data["muted"].setdefault(gid, [])
    if uid not in data["muted"][gid]:
        data["muted"][gid].append(uid)
        bot.restrict_chat_member(m.chat.id, int(uid), can_send_messages=False)
        bot.reply_to(m, f"🔇 کاربر {m.reply_to_message.from_user.first_name} به سکوت رفت.")
    save_data(data)

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("اخطار ") and m.reply_to_message)
def warn_user(m):
    data = load_data(); gid = str(m.chat.id)
    uid = str(m.reply_to_message.from_user.id)
    data["warns"].setdefault(gid, {})
    data["warns"][gid][uid] = data["warns"][gid].get(uid, 0) + 1
    save_data(data)
    warns = data["warns"][gid][uid]
    msg = f"⚠️ به {m.reply_to_message.from_user.first_name} اخطار داده شد. (تعداد: {warns})"
    if warns >= 3:
        bot.ban_chat_member(m.chat.id, int(uid))
        msg += "\n🚫 به دلیل ۳ اخطار بن شد!"
    bot.reply_to(m, msg)

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست بن‌شده‌ها")
def list_banned(m):
    d = load_data(); gid = str(m.chat.id)
    lst = d["banned"].get(gid, [])
    if not lst: return bot.reply_to(m, "✅ هیچ کاربری بن نشده.")
    txt = "\n".join([f"{i+1}. <code>{u}</code>" for i,u in enumerate(lst)])
    bot.reply_to(m, "🚫 <b>لیست کاربران بن‌شده:</b>\n" + txt)

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست سکوت‌ها")
def list_muted(m):
    d = load_data(); gid = str(m.chat.id)
    lst = d["muted"].get(gid, [])
    if not lst: return bot.reply_to(m, "✅ کسی در سکوت نیست.")
    txt = "\n".join([f"{i+1}. <code>{u}</code>" for i,u in enumerate(lst)])
    bot.reply_to(m, "🔇 <b>لیست کاربران در سکوت:</b>\n" + txt)

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست اخطارها")
def list_warns(m):
    d = load_data(); gid = str(m.chat.id)
    warns = d["warns"].get(gid, {})
    if not warns: return bot.reply_to(m, "✅ هیچ اخطاری ثبت نشده.")
    txt = "\n".join([f"{i+1}. <code>{uid}</code> — {c} اخطار" for i, (uid, c) in enumerate(warns.items())])
    bot.reply_to(m, "⚠️ <b>لیست اخطارها:</b>\n" + txt)

# ================= 😂 جوک و 🔮 فال =================
@bot.message_handler(func=lambda m: cmd_text(m) == "جوک")
def joke(m):
    d = load_data(); j = d.get("jokes", [])
    bot.reply_to(m, random.choice(j) if j else "هیچ جوکی ثبت نشده 😅")

@bot.message_handler(func=lambda m: cmd_text(m) == "فال")
def fal(m):
    d = load_data(); f = d.get("falls", [])
    bot.reply_to(m, random.choice(f) if f else "فالی ثبت نشده 🔮")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "ثبت جوک" and m.reply_to_message)
def add_joke(m):
    d = load_data()
    d["jokes"].append(m.reply_to_message.text)
    save_data(d)
    bot.reply_to(m, "😂 جوک با موفقیت ذخیره شد.")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "ثبت فال" and m.reply_to_message)
def add_fal(m):
    d = load_data()
    d["falls"].append(m.reply_to_message.text)
    save_data(d)
    bot.reply_to(m, "🔮 فال جدید ذخیره شد.")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "لیست جوک‌ها")
def list_jokes(m):
    d = load_data(); j = d.get("jokes", [])
    txt = "\n".join([f"{i+1}. {x}" for i, x in enumerate(j)]) if j else "❗ جوکی نیست."
    bot.reply_to(m, "📜 <b>لیست جوک‌ها:</b>\n" + txt)

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "لیست فال‌ها")
def list_falls(m):
    d = load_data(); f = d.get("falls", [])
    txt = "\n".join([f"{i+1}. {x}" for i, x in enumerate(f)]) if f else "❗ فالی نیست."
    bot.reply_to(m, "📜 <b>لیست فال‌ها:</b>\n" + txt)

# ================= 📊 آمار و آیدی =================
@bot.message_handler(func=lambda m: cmd_text(m) == "آمار")
def stats(m):
    d = load_data(); gid = str(m.chat.id)
    st = d["stats"].get(gid, {})
    total = sum(st.get("counts", {}).values()) if st else 0
    msg = (
        f"📊 آمار امروز:\n"
        f"📅 {shamsi_date()} | ⏰ {shamsi_time()}\n"
        f"📨 مجموع پیام‌ها: {total}\n"
        f"💬 اعضای فعال: {len(st.get('users', {})) if st else 0}\n"
        f"🕒 آخرین بروز: {now_teh().strftime('%H:%M:%S')}"
    )
    bot.reply_to(m, msg)

@bot.message_handler(func=lambda m: cmd_text(m) == "آیدی")
def user_id(m):
    u = m.from_user
    photos = bot.get_user_profile_photos(u.id)
    if photos.total_count > 0:
        bot.send_photo(m.chat.id, photos.photos[0][-1].file_id,
                       caption=f"🧾 نام: {u.first_name}\n🆔 آیدی: <code>{u.id}</code>\n⏰ {shamsi_time()}")
    else:
        bot.reply_to(m, f"🆔 آیدی شما: <code>{u.id}</code>")

# ================= 🔗 لینک‌ها =================
@bot.message_handler(func=lambda m: cmd_text(m) == "لینک گروه")
def group_link(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        link = bot.export_chat_invite_link(m.chat.id)
        bot.reply_to(m, f"🔗 لینک گروه:\n{link}")
    except:
        bot.reply_to(m, "⚠️ امکان گرفتن لینک وجود ندارد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لینک ربات")
def bot_link(m):
    uname = bot.get_me().username
    bot.reply_to(m, f"🤖 لینک ربات:\nhttps://t.me/{uname}")

# ================= 🧹 پاکسازی =================
@bot.message_handler(func=lambda m: cmd_text(m).startswith("پاکسازی "))
def clear_msgs(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        num = int(m.text.split(" ")[1])
        for i in range(num):
            bot.delete_message(m.chat.id, m.message_id - i)
        bot.send_message(m.chat.id, f"🧹 {num} پیام حذف شد ✅")
    except:
        bot.reply_to(m, "⚠️ عدد معتبر وارد کنید.")

# ================= 📢 ارسال همگانی (فقط سودو) =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ارسال" and m.reply_to_message)
def broadcast(m):
    d = load_data()
    users = list(set(d.get("users", [])))
    groups = [int(g) for g in d.get("welcome", {}).keys()]
    msg = m.reply_to_message; total = 0
    for uid in users + groups:
        try:
            if msg.text: bot.send_message(uid, msg.text)
            elif msg.photo: bot.send_photo(uid, msg.photo[-1].file_id, caption=msg.caption or "")
            total += 1
        except: continue
    bot.reply_to(m, f"📢 پیام به {total} گروه/کاربر ارسال شد.")

# ================= 👑 پاسخ سودو =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).lower() in ["سلام","ربات","bot"])
def sudo_reply(m):
    bot.reply_to(m, f"سلام 👑 {m.from_user.first_name}!\nدر خدمتتم سودوی عزیز 🤖")

# ================= 🚀 اجرای ربات =================
if __name__ == "__main__":
    print("🤖 ربات مدیریتی فارسی Lux V15.0 – فعال شد ✅")
    bot.infinity_polling(timeout=60, long_polling_timeout=30)
