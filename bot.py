# -*- coding: utf-8 -*-
# ✨ Persian Lux Panel – Part 1/2
# 👑 ساخته شده مخصوص محمد – نسخه لوکس با تمام قابلیت‌ها

import os, json, random, logging, time
from datetime import datetime
import pytz, jdatetime
import telebot
from telebot import types

# ================= ⚙️ تنظیمات اولیه =================
TOKEN   = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

DATA_FILE = "data.json"
LOG_FILE  = "error.log"
logging.basicConfig(filename=LOG_FILE, level=logging.ERROR,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# ================= 📂 ساختار داده‌ها =================
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
        "falls": [],
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

# ================= 🕒 زمان شمسی =================
def now_teh():
    return datetime.now(pytz.timezone("Asia/Tehran"))

def shamsi_date():
    return jdatetime.datetime.now().strftime("%A %d %B %Y")

def shamsi_time():
    return jdatetime.datetime.now().strftime("%H:%M:%S")

# ================= 📌 ابزارها =================
def cmd_text(m):
    return (getattr(m, "text", None) or "").strip()

def is_sudo(uid):
    d = load_data()
    return str(uid) in [str(SUDO_ID)] + [str(x) for x in d.get("sudo_list", [])]

def is_admin(chat_id, uid):
    d = load_data()
    gid = str(chat_id)
    if is_sudo(uid):
        return True
    if str(uid) in d["admins"].get(gid, []):
        return True
    try:
        st = bot.get_chat_member(chat_id, uid).status
        return st in ("administrator", "creator")
    except:
        return False

def register_group(gid):
    data = load_data()
    gid = str(gid)
    data["welcome"].setdefault(gid, {"enabled": True, "type": "text", "content": None, "file_id": None})
    data["locks"].setdefault(gid, {k: False for k in ["link","group","photo","video","sticker","gif","file","music","voice","forward"]})
    save_data(data)

# ================= 🚀 استارت =================
@bot.message_handler(commands=["start"])
def start_cmd(m):
    d = load_data()
    u = str(m.from_user.id)
    if u not in d["users"]:
        d["users"].append(u)
        save_data(d)
    bot.reply_to(m, "👋 سلام {}\nبه ربات مدیریتی خوش اومدی 🌟\nبرای ورود به پنل بنویس: <b>پنل</b> یا /panel".format(m.from_user.first_name))

# ================= 💬 آیدی / ساعت / لینک =================
@bot.message_handler(func=lambda m: cmd_text(m) in ["آیدی","ایدی"])
def show_id(m):
    try:
        caption = (
            f"🧾 <b>نام:</b> {m.from_user.first_name}\n"
            f"🆔 <b>آیدی شما:</b> <code>{m.from_user.id}</code>\n"
            f"💬 <b>آیدی گروه:</b> <code>{m.chat.id}</code>\n"
            f"📅 {shamsi_date()} | ⏰ {shamsi_time()}"
        )
        ph = bot.get_user_profile_photos(m.from_user.id, limit=1)
        if ph.total_count > 0:
            bot.send_photo(m.chat.id, ph.photos[0][-1].file_id, caption=caption)
        else:
            bot.reply_to(m, caption)
    except Exception as e:
        bot.reply_to(m, f"🆔 <code>{m.from_user.id}</code> | ⏰ {shamsi_time()}")

@bot.message_handler(func=lambda m: cmd_text(m) == "ساعت")
def show_time(m):
    bot.reply_to(m, f"⏰ ساعت فعلی: {shamsi_time()}\n📅 تاریخ: {shamsi_date()}")

@bot.message_handler(func=lambda m: cmd_text(m) == "لینک گروه")
def group_link(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        link = bot.export_chat_invite_link(m.chat.id)
        bot.reply_to(m, f"🔗 لینک گروه:\n{link}")
    except:
        bot.reply_to(m, "⚠️ دسترسی ساخت لینک ندارم.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لینک ربات")
def bot_link(m):
    bot.reply_to(m, f"🤖 لینک ربات:\nhttps://t.me/{bot.get_me().username}")

# ================= 👋 خوشامد =================
@bot.message_handler(content_types=["new_chat_members"])
def welcome(m):
    register_group(m.chat.id)
    d = load_data()
    gid = str(m.chat.id)
    s = d["welcome"].get(gid, {"enabled": True})
    if not s.get("enabled", True): return
    user = m.new_chat_members[0]
    name = user.first_name or "دوست جدید"
    t = shamsi_time()
    text = s.get("content") or f"سلام {name} 🌹\nبه <b>{m.chat.title}</b> خوش اومدی 🌸\n⏰ {t}"
    text = text.replace("{name}", name).replace("{time}", t)
    if s.get("file_id"):
        bot.send_photo(m.chat.id, s["file_id"], caption=text)
    else:
        bot.send_message(m.chat.id, text)

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "تنظیم خوشامد")
def set_welcome(m):
    d = load_data()
    gid = str(m.chat.id)
    msg = m.reply_to_message
    if msg.photo:
        fid = msg.photo[-1].file_id
        d["welcome"][gid] = {"enabled": True, "type": "photo", "content": msg.caption or "", "file_id": fid}
    elif msg.text:
        d["welcome"][gid] = {"enabled": True, "type": "text", "content": msg.text, "file_id": None}
    save_data(d)
    bot.reply_to(m, "✅ پیام خوشامد جدید ذخیره شد.\nاز {name} و {time} هم می‌تونی استفاده کنی.")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) in ["خوشامد روشن", "خوشامد خاموش"])
def toggle_welcome(m):
    d = load_data()
    gid = str(m.chat.id)
    en = cmd_text(m) == "خوشامد روشن"
    d["welcome"].setdefault(gid, {"enabled": True})
    d["welcome"][gid]["enabled"] = en
    save_data(d)
    bot.reply_to(m, "🌕 خوشامد فعال شد." if en else "🌑 خوشامد غیرفعال شد.")

# ================= 🔒 قفل‌ها =================
LOCK_MAP = {
    "لینک": "link","گروه": "group","عکس": "photo","ویدیو": "video",
    "استیکر": "sticker","گیف": "gif","فایل": "file",
    "موزیک": "music","ویس": "voice","فوروارد": "forward"
}

@bot.message_handler(func=lambda m: cmd_text(m).startswith("قفل ") or cmd_text(m).startswith("بازکردن "))
def toggle_lock(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    d = load_data(); gid = str(m.chat.id)
    part = cmd_text(m).split(" ")
    if len(part) < 2: return
    key_fa = part[1]
    lock_type = LOCK_MAP.get(key_fa)
    if not lock_type:
        return bot.reply_to(m, "❌ نوع قفل نامعتبر است.")
    en = cmd_text(m).startswith("قفل ")
    d["locks"].setdefault(gid, {k: False for k in LOCK_MAP.values()})
    if d["locks"][gid][lock_type] == en:
        return bot.reply_to(m, "⚠️ همین الان هم همین وضعیت است.")
    d["locks"][gid][lock_type] = en; save_data(d)
    if lock_type == "group":
        bot.send_message(m.chat.id, "🔒 گروه بسته شد." if en else "🔓 گروه باز شد.")
    else:
        bot.reply_to(m, f"{'🔒' if en else '🔓'} قفل {key_fa} {'فعال' if en else 'غیرفعال'} شد.")# ================= 🚫 بن / سکوت / اخطار =================
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "بن")
def ban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    if is_sudo(uid): return bot.reply_to(m, "⚡ نمی‌توان سودو را بن کرد.")
    try:
        bot.ban_chat_member(m.chat.id, uid)
        bot.reply_to(m, f"🚫 کاربر <b>{m.reply_to_message.from_user.first_name}</b> بن شد.")
    except:
        bot.reply_to(m, "❗ خطا در انجام بن.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف بن")
def unban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.unban_chat_member(m.chat.id, m.reply_to_message.from_user.id)
        bot.reply_to(m, "✅ کاربر از بن خارج شد.")
    except:
        bot.reply_to(m, "❗ خطا در حذف بن.")

# ================= 😂 جوک / 🔮 فال =================
@bot.message_handler(func=lambda m: cmd_text(m) == "جوک")
def send_joke(m):
    d = load_data(); jokes = d.get("jokes", [])
    if not jokes: return bot.reply_to(m, "😅 هنوز جوکی ثبت نشده.")
    bot.reply_to(m, random.choice(jokes))

@bot.message_handler(func=lambda m: cmd_text(m) == "فال")
def send_fal(m):
    d = load_data(); falls = d.get("falls", [])
    if not falls: return bot.reply_to(m, "🔮 هنوز فالی ثبت نشده.")
    bot.reply_to(m, random.choice(falls))

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "ثبت جوک")
def add_joke(m):
    d = load_data()
    txt = (m.reply_to_message.text or "").strip()
    if not txt: return bot.reply_to(m, "⚠️ فقط متن رو ریپلای کن.")
    d["jokes"].append(txt); save_data(d)
    bot.reply_to(m, "😂 جوک با موفقیت ثبت شد.")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "ثبت فال")
def add_fal(m):
    d = load_data()
    txt = (m.reply_to_message.text or "").strip()
    if not txt: return bot.reply_to(m, "⚠️ فقط متن رو ریپلای کن.")
    d["falls"].append(txt); save_data(d)
    bot.reply_to(m, "🔮 فال با موفقیت ذخیره شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست جوک‌ها")
def list_jokes(m):
    d = load_data(); jokes = d.get("jokes", [])
    if not jokes: return bot.reply_to(m, "❗ هیچ جوکی ثبت نشده.")
    txt = "\n".join([f"{i+1}. {t}" for i,t in enumerate(jokes)])
    bot.reply_to(m, "😂 <b>لیست جوک‌ها:</b>\n" + txt)

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست فال‌ها")
def list_fals(m):
    d = load_data(); falls = d.get("falls", [])
    if not falls: return bot.reply_to(m, "❗ هیچ فالی ثبت نشده.")
    txt = "\n".join([f"{i+1}. {t}" for i,t in enumerate(falls)])
    bot.reply_to(m, "🔮 <b>لیست فال‌ها:</b>\n" + txt)

# ================= 📊 آمار روزانه =================
@bot.message_handler(func=lambda m: cmd_text(m) == "آمار")
def group_stats(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    d = load_data(); gid = str(m.chat.id)
    register_group(gid)
    st = d["stats"].get(gid, {})
    today = shamsi_date(); hour = shamsi_time()
    counts = st.get("counts", {k:0 for k in ["msg","photo","video","voice","music","sticker","gif","fwd"]})
    total = sum(counts.values())
    if st.get("users"):
        top_uid = max(st["users"], key=st["users"].get)
        try:
            top_name = bot.get_chat_member(m.chat.id, int(top_uid)).user.first_name
        except:
            top_name = top_uid
        top_line = f"🥇 فعال‌ترین عضو: {top_name} ({st['users'][top_uid]} پیام)"
    else:
        top_line = "⛔ هنوز فعالیتی ثبت نشده."
    msg = f"""📊 <b>آمار امروز</b>
📅 {today} | ⏰ {hour}
━━━━━━━━━━━━━━
💬 کل پیام‌ها: {total}
🖼 عکس: {counts['photo']} | 🎬 ویدیو: {counts['video']}
🎵 موزیک: {counts['music']} | 🎙 ویس: {counts['voice']}
😜 استیکر: {counts['sticker']} | 🎞 گیف: {counts['gif']}
⚠️ فوروارد: {counts['fwd']}
━━━━━━━━━━━━━━
{top_line}"""
    bot.reply_to(m, msg)

# ================= 🧹 پاکسازی =================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("حذف "))
def delete_msgs(m):
    try:
        n = int(cmd_text(m).split()[1])
    except:
        return bot.reply_to(m, "❗ فرمت درست: حذف 20")
    count = 0
    for i in range(1, n+1):
        try:
            bot.delete_message(m.chat.id, m.message_id - i); count += 1
        except:
            continue
    bot.send_message(m.chat.id, f"🧹 {count} پیام پاک شد.", disable_notification=True)

# ================= 📢 ارسال همگانی =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ارسال" and m.reply_to_message)
def broadcast(m):
    d = load_data()
    users = list(set(d.get("users", [])))
    groups = [int(g) for g in d["welcome"].keys()]
    total = 0
    msg = m.reply_to_message
    for uid in users + groups:
        try:
            if msg.text:
                bot.send_message(uid, msg.text)
            elif msg.photo:
                bot.send_photo(uid, msg.photo[-1].file_id, caption=msg.caption or "")
            total += 1
        except:
            continue
    bot.reply_to(m, f"📣 پیام برای {total} کاربر ارسال شد.")

# ================= 🤖 پاسخ سودو =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).lower() in ["سلام","ربات","bot","هی","چطوری"])
def sudo_reply(m):
    answers = [
        f"👑 سلام {m.from_user.first_name}! همیشه در خدمتتم سودو 🌟",
        f"🤖 جانم {m.from_user.first_name}! آماده‌ام ✨",
        f"💫 خوش اومدی {m.from_user.first_name}، چی دستور میدی؟",
        f"🔥 در خدمتتم رئیس {m.from_user.first_name}!"
    ]
    bot.reply_to(m, random.choice(answers))

# ================= 🎛️ پنل =================
def main_panel():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🔒 قفل‌ها", callback_data="locks"),
        types.InlineKeyboardButton("👋 خوشامد", callback_data="welcome"),
        types.InlineKeyboardButton("😂 جوک و فال", callback_data="fun"),
        types.InlineKeyboardButton("📊 آمار", callback_data="stats"),
        types.InlineKeyboardButton("📢 ارسال", callback_data="broadcast"),
        types.InlineKeyboardButton("🧹 پاکسازی", callback_data="clear"),
        types.InlineKeyboardButton("ℹ️ راهنما", callback_data="help"),
    )
    return kb

@bot.message_handler(commands=["panel","پنل"])
def open_panel(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    bot.send_message(m.chat.id, "🎛️ <b>پنل مدیریتی فعال شد!</b>\nاز دکمه‌های زیر استفاده کن 👇", reply_markup=main_panel())

@bot.callback_query_handler(func=lambda call: call.data == "help")
def help_panel(call):
    txt = (
        "📘 <b>راهنمای سریع:</b>\n"
        "• آیدی / ساعت / آمار / لینک‌ها\n"
        "• خوشامد روشن/خاموش + تنظیم خوشامد\n"
        "• قفل عکس، فیلم، گیف، لینک و ...\n"
        "• ثبت جوک / فال + لیست آن‌ها\n"
        "• ارسال همگانی و پاکسازی پیام‌ها\n"
        "• افزودن مدیر / سودو / بن کاربر"
    )
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, reply_markup=main_panel())

# ================= 🚀 اجرای ربات =================
if __name__ == "__main__":
    print("🤖 Persian Lux Panel فعال شد – نسخه کامل محمد 👑")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            time.sleep(5)
