# -*- coding: utf-8 -*-
# Persian Lux Panel V15 – Part 1/2
# Designed for Mohammad 👑

import os, json, random, time, logging
from datetime import datetime
import pytz, jdatetime
import telebot
from telebot import types

# ================= ⚙️ تنظیمات پایه =================
TOKEN   = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
bot     = telebot.TeleBot(TOKEN, parse_mode="HTML")

DATA_FILE = "data.json"
LOG_FILE  = "error.log"
logging.basicConfig(filename=LOG_FILE, level=logging.ERROR,
                    format="%(asctime)s - %(levelname)s - %(message)s")

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
        "falls": []
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
    data["locks"].setdefault(gid, {k: False for k in ["link","group","photo","video","sticker","gif","file","music","voice","forward"]})
    save_data(data)

# ================= 🧩 ابزارها =================
def now_teh():
    return datetime.now(pytz.timezone("Asia/Tehran"))

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
    if is_sudo(uid): return True
    if str(uid) in d["admins"].get(gid, []): return True
    try:
        st = bot.get_chat_member(chat_id, uid).status
        return st in ("administrator", "creator")
    except:
        return False

# ================= 👋 خوشامد =================
@bot.message_handler(content_types=["new_chat_members"])
def welcome_new(m):
    register_group(m.chat.id)
    data = load_data(); gid = str(m.chat.id)
    s = data["welcome"].get(gid, {"enabled": True})
    if not s.get("enabled", True): return
    user = m.new_chat_members[0]
    name = user.first_name or "دوست جدید"
    text = s.get("content") or f"✨ سلام {name}!\nبه گروه <b>{m.chat.title}</b> خوش اومدی 🌸\n⏰ {shamsi_time()}"
    text = text.replace("{name}", name).replace("{time}", shamsi_time())
    if s.get("file_id"):
        bot.send_photo(m.chat.id, s["file_id"], caption=text)
    else:
        bot.send_message(m.chat.id, text)

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "تنظیم خوشامد")
def set_welcome(m):
    data = load_data(); gid = str(m.chat.id)
    msg = m.reply_to_message
    if msg.photo:
        fid = msg.photo[-1].file_id
        data["welcome"][gid] = {"enabled": True, "type": "photo", "content": msg.caption or "", "file_id": fid}
    elif msg.text:
        data["welcome"][gid] = {"enabled": True, "type": "text", "content": msg.text, "file_id": None}
    save_data(data)
    bot.reply_to(m, "✅ پیام خوشامد جدید تنظیم شد.\nاز {name} و {time} در متن می‌تونی استفاده کنی.")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) in ["خوشامد روشن","خوشامد خاموش"])
def toggle_welcome(m):
    data = load_data(); gid = str(m.chat.id)
    en = cmd_text(m) == "خوشامد روشن"
    data["welcome"].setdefault(gid, {"enabled": True})
    data["welcome"][gid]["enabled"] = en
    save_data(data)
    bot.reply_to(m, "🟢 خوشامد روشن شد." if en else "🔴 خوشامد خاموش شد.")

# ================= 🔒 قفل‌ها =================
LOCK_MAP = {
    "لینک": "link", "گروه": "group", "عکس": "photo", "ویدیو": "video",
    "استیکر": "sticker", "گیف": "gif", "فایل": "file",
    "موزیک": "music", "ویس": "voice", "فوروارد": "forward"
}

@bot.message_handler(func=lambda m: cmd_text(m).startswith("قفل ") or cmd_text(m).startswith("بازکردن "))
def toggle_lock(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    d = load_data(); gid = str(m.chat.id)
    part = cmd_text(m).split(" ")
    if len(part) < 2: return
    key_fa = part[1]
    lock_type = LOCK_MAP.get(key_fa)
    if not lock_type: return bot.reply_to(m, "❌ نوع قفل نامعتبر است.")
    en = cmd_text(m).startswith("قفل ")
    d["locks"].setdefault(gid, {k: False for k in LOCK_MAP.values()})
    if d["locks"][gid][lock_type] == en:
        return bot.reply_to(m, "⚠️ این قفل همین حالا هم در همین حالت است.")
    d["locks"][gid][lock_type] = en
    save_data(d)
    if lock_type == "group":
        bot.send_message(m.chat.id, "🔒 گروه بسته شد." if en else "🔓 گروه باز شد.")
    else:
        bot.reply_to(m, f"{'🔒' if en else '🔓'} قفل {key_fa} {'فعال' if en else 'غیرفعال'} شد.")

# ================= 👑 مدیر و سودو =================
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "افزودن مدیر")
def add_admin(m):
    if not is_sudo(m.from_user.id): return
    data = load_data(); gid = str(m.chat.id)
    uid = str(m.reply_to_message.from_user.id)
    data["admins"].setdefault(gid, [])
    if uid in data["admins"][gid]:
        return bot.reply_to(m, "⚠️ این کاربر از قبل مدیر است.")
    data["admins"][gid].append(uid)
    save_data(data)
    bot.reply_to(m, f"✅ کاربر <code>{uid}</code> به مدیران افزوده شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف مدیر")
def del_admin(m):
    if not is_sudo(m.from_user.id): return
    data = load_data(); gid = str(m.chat.id)
    uid = str(m.reply_to_message.from_user.id)
    if uid not in data["admins"].get(gid, []):
        return bot.reply_to(m, "❌ این کاربر در لیست مدیران نیست.")
    data["admins"][gid].remove(uid)
    save_data(data)
    bot.reply_to(m, "🗑 مدیر حذف شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست مدیران")
def list_admins(m):
    data = load_data(); gid = str(m.chat.id)
    lst = data["admins"].get(gid, [])
    if not lst:
        return bot.reply_to(m, "📋 هنوز مدیری ثبت نشده.")
    msg = "👑 لیست مدیران:\n" + "\n".join([f"• <a href='tg://user?id={a}'>کاربر {a}</a>" for a in lst])
    bot.reply_to(m, msg)

# ---- سودو ----
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "افزودن سودو")
def add_sudo(m):
    if m.from_user.id != SUDO_ID: return
    d = load_data(); uid = str(m.reply_to_message.from_user.id)
    if uid in d["sudo_list"]: return bot.reply_to(m, "⚠️ این کاربر از قبل سودو است.")
    d["sudo_list"].append(uid); save_data(d)
    bot.reply_to(m, f"✅ <a href='tg://user?id={uid}'>کاربر</a> به لیست سودوها اضافه شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست سودو")
def list_sudos(m):
    if not is_sudo(m.from_user.id): return
    d = load_data(); s = d.get("sudo_list", [])
    if not s: return bot.reply_to(m, "❗ هیچ سودویی ثبت نشده.")
    txt = "👑 لیست سودوها:\n" + "\n".join([f"• <a href='tg://user?id={x}'>کاربر {x}</a>" for x in s])
    bot.reply_to(m, txt)

# ================= 🎛 پنل شیشه‌ای =================
def main_panel():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🔒 قفل‌ها", callback_data="locks"),
        types.InlineKeyboardButton("👋 خوشامد", callback_data="welcome"),
        types.InlineKeyboardButton("👑 مدیران", callback_data="admins"),
        types.InlineKeyboardButton("🧠 سودوها", callback_data="sudos"),
        types.InlineKeyboardButton("ℹ️ راهنما", callback_data="help"),
        types.InlineKeyboardButton("🔚 بستن", callback_data="close")
    )
    return kb

@bot.message_handler(commands=["panel","پنل"])
def open_panel(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    bot.send_message(
        m.chat.id,
        "🎛 <b>پنل مدیریتی Persian Lux Panel</b>\nاز دکمه‌های زیر استفاده کنید 👇",
        reply_markup=main_panel()
    )

@bot.callback_query_handler(func=lambda c: True)
def cb_panel(call):
    try:
        if call.data == "close":
            bot.delete_message(call.message.chat.id, call.message.message_id)
        elif call.data == "help":
            txt = (
                "📘 <b>راهنمای سریع:</b>\n"
                "• آیدی، ساعت، آمار\n"
                "• قفل / بازکردن لینک، عکس، فیلم...\n"
                "• خوشامد روشن/خاموش + تنظیم\n"
                "• افزودن مدیر / سودو + لیست‌ها\n"
                "• ثبت جوک / فال / پاکسازی / ارسال همگانی\n"
                "• بن، سکوت، اخطار و ...\n\n"
                "👑 Persian Lux Panel V15"
            )
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="main"))
            bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, reply_markup=kb)
        elif call.data == "main":
            bot.edit_message_text("🎛 منوی اصلی:", call.message.chat.id, call.message.message_id, reply_markup=main_panel())
    except Exception as e:
        logging.error(f"callback error: {e}")# ================ 😂 جوک و 🔮 فال =================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "ثبت جوک")
def add_joke(m):
    d = load_data()
    txt = (m.reply_to_message.text or "").strip()
    if not txt: return bot.reply_to(m, "⚠️ لطفاً روی پیام متنی ریپلای کن.")
    d["jokes"].append(txt); save_data(d)
    bot.reply_to(m, "😂 جوک ذخیره شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "جوک")
def random_joke(m):
    d = load_data(); jokes = d.get("jokes", [])
    if not jokes: return bot.reply_to(m, "😅 هنوز جوکی ثبت نشده.")
    bot.reply_to(m, f"😂 {random.choice(jokes)}")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست جوک")
def list_jokes(m):
    d = load_data(); jokes = d.get("jokes", [])
    if not jokes: return bot.reply_to(m, "❗ هیچ جوکی ثبت نشده.")
    text = "\n".join([f"{i+1}. {j}" for i, j in enumerate(jokes)])
    bot.reply_to(m, f"📜 لیست جوک‌ها:\n{text}")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("حذف جوک "))
def del_joke(m):
    d = load_data(); jokes = d.get("jokes", [])
    try:
        idx = int(cmd_text(m).split()[2]) - 1
        if idx < 0 or idx >= len(jokes): raise ValueError
        removed = jokes.pop(idx); save_data(d)
        bot.reply_to(m, f"🗑 جوک حذف شد:\n{removed}")
    except:
        bot.reply_to(m, "❗ شماره‌ی جوک نامعتبر است.")

# ==== فال ====
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "ثبت فال")
def add_fal(m):
    d = load_data()
    txt = (m.reply_to_message.text or "").strip()
    if not txt: return bot.reply_to(m, "⚠️ لطفاً روی پیام متنی ریپلای کن.")
    d["falls"].append(txt); save_data(d)
    bot.reply_to(m, "🔮 فال ذخیره شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "فال")
def random_fal(m):
    d = load_data(); f = d.get("falls", [])
    if not f: return bot.reply_to(m, "😅 هنوز فالی ثبت نشده.")
    bot.reply_to(m, f"🔮 {random.choice(f)}")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست فال")
def list_fals(m):
    d = load_data(); f = d.get("falls", [])
    if not f: return bot.reply_to(m, "❗ هیچ فالی ثبت نشده.")
    text = "\n".join([f"{i+1}. {x}" for i, x in enumerate(f)])
    bot.reply_to(m, f"📜 لیست فال‌ها:\n{text}")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("حذف فال "))
def del_fal(m):
    d = load_data(); f = d.get("falls", [])
    try:
        idx = int(cmd_text(m).split()[2]) - 1
        if idx < 0 or idx >= len(f): raise ValueError
        removed = f.pop(idx); save_data(d)
        bot.reply_to(m, f"🗑 فال حذف شد:\n{removed}")
    except:
        bot.reply_to(m, "❗ شماره‌ی فال نامعتبر است.")

# ================ 🚫 بن / سکوت / اخطار =================
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "بن")
def ban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    if is_sudo(uid): return bot.reply_to(m, "⚡ نمی‌توان سودو را بن کرد.")
    try:
        bot.ban_chat_member(m.chat.id, uid)
        bot.reply_to(m, f"🚫 کاربر <a href='tg://user?id={uid}'>بن</a> شد.")
    except:
        bot.reply_to(m, "❗ خطا در بن کاربر.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف بن")
def unban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.unban_chat_member(m.chat.id, m.reply_to_message.from_user.id, only_if_banned=True)
        bot.reply_to(m, "✅ کاربر از بن خارج شد.")
    except:
        bot.reply_to(m, "❗ خطا در حذف بن.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "سکوت")
def mute_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = str(m.reply_to_message.from_user.id)
    d = load_data(); d["muted"][uid] = True; save_data(d)
    bot.reply_to(m, f"🔇 کاربر <a href='tg://user?id={uid}'>ساکت</a> شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف سکوت")
def unmute_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = str(m.reply_to_message.from_user.id)
    d = load_data()
    if uid in d["muted"]: d["muted"].pop(uid)
    save_data(d)
    bot.reply_to(m, f"🔊 سکوت کاربر <a href='tg://user?id={uid}'>برداشته</a> شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "اخطار")
def warn_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = str(m.reply_to_message.from_user.id)
    d = load_data(); d["warns"][uid] = d["warns"].get(uid, 0) + 1; save_data(d)
    count = d["warns"][uid]
    msg = f"⚠️ کاربر <a href='tg://user?id={uid}'>اخطار {count}</a> گرفت."
    if count >= 3:
        bot.ban_chat_member(m.chat.id, int(uid))
        msg += "\n🚫 چون ۳ اخطار گرفت، از گروه اخراج شد."
    bot.reply_to(m, msg)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف اخطار")
def del_warn(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = str(m.reply_to_message.from_user.id)
    d = load_data()
    if uid in d["warns"]: d["warns"].pop(uid)
    save_data(d)
    bot.reply_to(m, "✅ تمام اخطارهای کاربر پاک شد.")

# ================ 📊 آمار =================
@bot.message_handler(func=lambda m: cmd_text(m) == "آمار")
def group_stats(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    d = load_data(); gid = str(m.chat.id)
    try:
        count = bot.get_chat_member_count(m.chat.id)
    except:
        count = "نامشخص"
    msg = (
        f"📊 <b>آمار گروه</b>\n"
        f"👥 اعضا: {count}\n"
        f"📅 تاریخ: {shamsi_date()}\n"
        f"⏰ ساعت: {shamsi_time()}\n"
        f"💬 کل پیام‌های امروز ثبت‌شده: فعال"
    )
    bot.reply_to(m, msg)

# ================ 🧹 پاکسازی =================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("حذف "))
def del_msgs(m):
    try:
        n = int(cmd_text(m).split()[1])
    except:
        return bot.reply_to(m, "❗ فرمت درست: حذف 20")
    for i in range(1, n+1):
        try: bot.delete_message(m.chat.id, m.message_id - i)
        except: pass
    bot.send_message(m.chat.id, f"🧹 {n} پیام پاک شد.", disable_notification=True)

# ================ 📢 ارسال همگانی =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and m.reply_to_message and cmd_text(m) == "ارسال")
def broadcast(m):
    d = load_data()
    users = list(set(d.get("users", [])))
    groups = [int(g) for g in d["welcome"].keys()]
    msg = m.reply_to_message
    total = 0
    for uid in users + groups:
        try:
            if msg.text:
                bot.send_message(uid, msg.text)
            elif msg.photo:
                bot.send_photo(uid, msg.photo[-1].file_id, caption=msg.caption or "")
            total += 1
        except: continue
    bot.reply_to(m, f"📢 پیام برای {total} مخاطب ارسال شد.")

# ================ 🤖 پاسخ سودو =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).lower() in ["سلام","ربات","هی","bot"])
def sudo_reply(m):
    replies = [
        f"👑 جانم {m.from_user.first_name}، در خدمتتم 💎",
        f"✨ سلام {m.from_user.first_name}! آماده‌ام 💪",
        f"🤖 بله {m.from_user.first_name}، گوش به فرمانم 🔥"
    ]
    bot.reply_to(m, random.choice(replies))

# ================ 🚀 اجرای نهایی =================
@bot.message_handler(commands=["start"])
def start_cmd(m):
    d = load_data()
    uid = str(m.from_user.id)
    if uid not in d["users"]:
        d["users"].append(uid); save_data(d)
    bot.reply_to(m, "✨ ربات مدیریتی Persian Lux Panel فعال است.\nبرای دسترسی به امکانات بنویس: «پنل» یا /panel")

if __name__ == "__main__":
    print("🤖 Persian Lux Panel V15 is running...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            logging.error(f"polling crash: {e}")
            time.sleep(5)
