# -*- coding: utf-8 -*-
import os, json, random, logging
from datetime import datetime
import pytz, jdatetime
import telebot
from telebot import types

# ================= ⚙️ تنظیمات پایه =================
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
def now_teh():
    return datetime.now(pytz.timezone("Asia/Tehran"))

def shamsi_date():
    return jdatetime.datetime.now().strftime("%A %d %B %Y")

def shamsi_time():
    return jdatetime.datetime.now().strftime("%H:%M:%S")

# ================= 🧱 ثبت گروه =================
def register_group(gid):
    data = load_data()
    gid = str(gid)
    data["welcome"].setdefault(gid, {"enabled": True, "type": "text", "content": None, "file_id": None})
    data["locks"].setdefault(gid, {k: False for k in LOCK_MAP.values()})
    if gid not in data["stats"]:
        data["stats"][gid] = {
            "date": str(datetime.now().date()),
            "users": {},
            "counts": {k: 0 for k in ["msg","photo","video","voice","music","sticker","gif","fwd"]}
        }
    save_data(data)

# ================= ⚙️ ابزارها =================
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

# ================= 💬 آیدی و ساعت =================
@bot.message_handler(func=lambda m: cmd_text(m) in ["آیدی","ایدی"])
def cmd_id(m):
    try:
        photos = bot.get_user_profile_photos(m.from_user.id, limit=1)
        caption = (
            f"🆔 آیدی شما: <code>{m.from_user.id}</code>\n"
            f"💬 آیدی گروه: <code>{m.chat.id}</code>\n"
            f"⏰ ساعت: {shamsi_time()}\n📅 تاریخ: {shamsi_date()}"
        )
        if photos.total_count > 0:
            bot.send_photo(m.chat.id, photos.photos[0][-1].file_id, caption=caption)
        else:
            bot.reply_to(m, caption)
    except Exception as e:
        logging.error(f"ID error: {e}")
        bot.reply_to(m, "❗ خطا در دریافت آیدی.")

@bot.message_handler(func=lambda m: cmd_text(m) == "ساعت")
def cmd_time(m):
    bot.reply_to(m, f"⏰ ساعت: {shamsi_time()}\n📅 تاریخ: {shamsi_date()}")

# ================= 🔗 لینک‌ها =================
@bot.message_handler(func=lambda m: cmd_text(m) == "لینک گروه")
def get_group_link(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        link = bot.export_chat_invite_link(m.chat.id)
        bot.reply_to(m, f"🔗 لینک گروه:\n{link}")
    except:
        bot.reply_to(m, "❗ خطا در دریافت لینک گروه.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لینک ربات")
def bot_link(m):
    bot.reply_to(m, f"🤖 لینک ربات:\nhttps://t.me/{bot.get_me().username}")

# ================= 👋 خوشامد =================
@bot.message_handler(content_types=["new_chat_members"])
def welcome(m):
    register_group(m.chat.id)
    data = load_data(); gid = str(m.chat.id)
    s = data["welcome"].get(gid, {"enabled": True})
    if not s.get("enabled", True): return
    user = m.new_chat_members[0]
    name = user.first_name or "دوست جدید"
    text = s.get("content") or f"سلام {name} 🌙\nبه گروه {m.chat.title} خوش اومدی 😎\n⏰ {shamsi_time()}"
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
        data["welcome"][gid] = {"enabled": True, "type": "photo", "content": msg.caption or " ", "file_id": fid}
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
    bot.reply_to(m, "🟢 خوشامد روشن شد" if en else "🔴 خوشامد خاموش شد")

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
        msg = "⚠️ از قبل همین حالت بود."
        return bot.reply_to(m, msg)
    data["locks"][gid][lock_type] = en
    save_data(data)
    if lock_type == "group":
        bot.send_message(m.chat.id, "🔒 گروه بسته شد." if en else "🔓 گروه باز شد.")
    else:
        bot.reply_to(m, f"🔐 قفل {key_fa} {'فعال' if en else 'غیرفعال'} شد.")

# ================= 🚫 بن و سکوت و اخطار =================
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "بن")
def ban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    if is_sudo(uid): return bot.reply_to(m, "⚡ نمی‌توان سودو را بن کرد.")
    try:
        bot.ban_chat_member(m.chat.id, uid)
        bot.reply_to(m, f"🚫 کاربر {uid} بن شد.")
    except:
        bot.reply_to(m, "❗ خطا در بن.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف بن")
def unban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.unban_chat_member(m.chat.id, m.reply_to_message.from_user.id)
        bot.reply_to(m, "✅ کاربر از بن خارج شد.")
    except:
        bot.reply_to(m, "❗ خطا در حذف بن.")# ================= 😂 جوک و 🔮 فال =================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "ثبت جوک")
def add_joke(m):
    data = load_data()
    data["jokes"].append(m.reply_to_message.text)
    save_data(data)
    bot.reply_to(m, "😂 جوک با موفقیت ثبت شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "جوک")
def send_joke(m):
    data = load_data(); jokes = data.get("jokes", [])
    if not jokes: return bot.reply_to(m, "❗ هنوز جوکی ثبت نشده.")
    bot.reply_to(m, random.choice(jokes))

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "ثبت فال")
def add_fal(m):
    data = load_data()
    data["falls"].append(m.reply_to_message.text)
    save_data(data)
    bot.reply_to(m, "🔮 فال جدید ذخیره شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "فال")
def send_fal(m):
    data = load_data(); falls = data.get("falls", [])
    if not falls: return bot.reply_to(m, "❗ هنوز فالی ثبت نشده.")
    bot.reply_to(m, random.choice(falls))

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) in ["لیست جوک‌ها", "لیست جوک ها"])
def list_jokes(m):
    data = load_data(); jokes = data.get("jokes", [])
    if not jokes: return bot.reply_to(m, "❗ جوکی ثبت نشده.")
    txt = "\n".join([f"{i+1}. {t}" for i, t in enumerate(jokes)])
    bot.reply_to(m, "📜 لیست جوک‌ها:\n" + txt)

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) in ["لیست فال‌ها", "لیست فال ها"])
def list_fals(m):
    data = load_data(); falls = data.get("falls", [])
    if not falls: return bot.reply_to(m, "❗ فالی ثبت نشده.")
    txt = "\n".join([f"{i+1}. {t}" for i, t in enumerate(falls)])
    bot.reply_to(m, "📜 لیست فال‌ها:\n" + txt)

# ================= 📊 آمار روزانه =================
@bot.message_handler(func=lambda m: cmd_text(m) == "آمار")
def group_stats(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    d = load_data(); gid = str(m.chat.id)
    register_group(gid)
    st = d["stats"][gid]
    today = shamsi_date(); hour = shamsi_time()
    total = sum(st["counts"].values())
    if st["users"]:
        top_user_id = max(st["users"], key=st["users"].get)
        try:
            user = bot.get_chat_member(m.chat.id, int(top_user_id)).user.first_name
        except:
            user = f"{top_user_id}"
        top_user = f"• نفر اول🥇 : ({st['users'][top_user_id]} پیام | {user})"
    else:
        top_user = "هیچ فعالیتی ثبت نشده است!"
    msg = f"""♡ فعالیت‌های امروز تا این لحظه:
➲ تاریخ: {today}
➲ ساعت: {hour}
✛ کل پیام‌ها: {total}
✛ فوروارد: {st['counts']['fwd']}
✛ فیلم: {st['counts']['video']}
✛ آهنگ: {st['counts']['music']}
✛ ویس: {st['counts']['voice']}
✛ عکس: {st['counts']['photo']}
✛ گیف: {st['counts']['gif']}
✛ استیکر: {st['counts']['sticker']}
✶ فعال‌ترین اعضای گروه:
{top_user}
📆 آخرین بروز رسانی: {now_teh().strftime('%Y-%m-%d %H:%M:%S')}
"""
    bot.reply_to(m, msg)

# ================= 🧹 پاکسازی =================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("پاکسازی "))
def clear_messages(m):
    try:
        count = int(cmd_text(m).split()[1])
        for i in range(count):
            bot.delete_message(m.chat.id, m.message_id - i)
        bot.send_message(m.chat.id, f"🧼 {count} پیام حذف شد.", disable_notification=True)
    except:
        bot.reply_to(m, "❗ عدد نامعتبر است.")

# ================= 📢 ارسال همگانی =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and m.reply_to_message and cmd_text(m) == "ارسال")
def broadcast(m):
    data = load_data()
    all_users = list(set(data.get("users", [])))
    groups = list(data["welcome"].keys())
    total = 0
    msg = m.reply_to_message
    for uid in all_users + [int(g) for g in groups]:
        try:
            if msg.text:
                bot.send_message(uid, msg.text)
            elif msg.photo:
                bot.send_photo(uid, msg.photo[-1].file_id, caption=msg.caption or "")
            total += 1
        except:
            continue
    bot.reply_to(m, f"📣 پیام برای {total} کاربر ارسال شد.")

# ================= 👑 سودو پاسخ هوشمند =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).lower() in ["سلام", "ربات", "bot"])
def sudo_reply(m):
    bot.reply_to(m, f"سلام 👑 {m.from_user.first_name}!\nدر خدمتتم سودوی عزیز 🤖")

# ================= 🪄 ثبت کاربران =================
@bot.message_handler(commands=["start"])
def register_user(m):
    data = load_data()
    uid = str(m.from_user.id)
    if uid not in data["users"]:
        data["users"].append(uid)
        save_data(data)
    bot.reply_to(m, "🤖 ربات مدیریتی فعال است!\nاز پنل یا دستورات استفاده کن.")

# ================= 🎛️ پنل شیشه‌ای =================
def main_panel():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🔒 قفل‌ها", callback_data="locks"),
        types.InlineKeyboardButton("👋 خوشامد", callback_data="welcome"),
        types.InlineKeyboardButton("😂 جوک و فال", callback_data="fun"),
        types.InlineKeyboardButton("📊 آمار", callback_data="stats"),
        types.InlineKeyboardButton("🧹 پاکسازی", callback_data="clear"),
        types.InlineKeyboardButton("📢 ارسال", callback_data="broadcast"),
        types.InlineKeyboardButton("👑 سودوها", callback_data="sudos"),
        types.InlineKeyboardButton("ℹ️ راهنما", callback_data="help")
    )
    return kb

@bot.message_handler(commands=["panel", "پنل"])
def open_panel(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)):
        return
    bot.send_message(
        m.chat.id,
        "🎛️ <b>پنل مدیریتی فعال شد!</b>\nاز دکمه‌های زیر استفاده کنید 👇",
        reply_markup=main_panel()
    )

# ================= ℹ️ راهنما =================
@bot.callback_query_handler(func=lambda call: call.data == "help")
def help_panel(call):
    txt = (
        "📘 <b>راهنمای دستورات:</b>\n\n"
        "• قفل لینک، عکس، فایل، گیف، گروه، و ...\n"
        "• خوشامد روشن/خاموش + تنظیم متن یا عکس\n"
        "• ثبت جوک / فال + نمایش یا لیست آن‌ها\n"
        "• آمار روزانه گروه + کاربران فعال\n"
        "• ارسال همگانی پیام یا عکس\n"
        "• بن / سکوت / اخطار کاربران\n"
        "• پاکسازی عددی پیام‌ها\n"
        "• آیدی، ساعت و لینک گروه / ربات\n\n"
        "👑 مخصوص مدیران و سودو"
    )
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, reply_markup=main_panel())

# ================= 🚀 اجرای نهایی =================
if __name__ == "__main__":
    print("🤖 ربات مدیریتی V13 Persian Glass Edition با موفقیت فعال شد!")
    bot.infinity_polling(timeout=60, long_polling_timeout=30)
