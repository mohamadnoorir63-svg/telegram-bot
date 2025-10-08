# -*- coding: utf-8 -*-
import os, json, random, logging
from datetime import datetime
import pytz, jdatetime
import telebot
from telebot import types

# ================= ⚙️ تنظیمات =================
TOKEN = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
DATA_FILE = "data.json"
LOG_FILE = "error.log"

logging.basicConfig(filename=LOG_FILE, level=logging.ERROR,
                    format="%(asctime)s - %(levelname)s - %(message)s")

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

def now_teh(): return datetime.now(pytz.timezone("Asia/Tehran"))
def shamsi_date(): return jdatetime.datetime.now().strftime("%A %d %B %Y")
def shamsi_time(): return jdatetime.datetime.now().strftime("%H:%M:%S")

# ================= 🧩 ابزارها =================
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

# ================= 💬 عمومی =================
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
        bot.reply_to(m, "❗ خطا در دریافت اطلاعات آیدی.")

@bot.message_handler(func=lambda m: cmd_text(m) == "ساعت")
def cmd_time(m):
    bot.reply_to(m, f"⏰ تهران: {now_teh().strftime('%H:%M:%S')}\n📅 شمسی: {shamsi_date()}")

@bot.message_handler(func=lambda m: cmd_text(m) == "لینک ربات")
def bot_link(m):
    bot.reply_to(m, f"🤖 لینک ربات:\nhttps://t.me/{bot.get_me().username}")

@bot.message_handler(func=lambda m: cmd_text(m) == "لینک گروه")
def get_group_link(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        link = bot.export_chat_invite_link(m.chat.id)
        bot.reply_to(m, f"🔗 لینک گروه:\n{link}")
    except:
        bot.reply_to(m, "❗ خطا در دریافت لینک گروه.")

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

# ================= 💡 شروع طراحی پنل =================
@bot.message_handler(func=lambda m: cmd_text(m) == "پنل")
def open_panel(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔒 قفل‌ها", callback_data="panel_locks"),
        types.InlineKeyboardButton("🎉 خوشامد", callback_data="panel_welcome"),
        types.InlineKeyboardButton("📊 آمار", callback_data="panel_stats"),
        types.InlineKeyboardButton("😂 جوک و فال", callback_data="panel_fun"),
        types.InlineKeyboardButton("🧹 پاکسازی", callback_data="panel_clear"),
        types.InlineKeyboardButton("📢 ارسال همگانی", callback_data="panel_broadcast")
    )
    bot.send_message(m.chat.id, "🎛 <b>پنل مدیریتی ربات</b>\nگزینه‌ی مورد نظر را انتخاب کنید:", reply_markup=markup)# ================= ⚙️ عملکرد منوها =================
@bot.callback_query_handler(func=lambda c: c.data.startswith("panel_"))
def panel_control(call):
    data = load_data()
    gid = str(call.message.chat.id)

    if call.data == "panel_locks":
        txt = "🔒 <b>مدیریت قفل‌ها</b>\nبرای فعال/غیرفعال کردن قفل از دستورات استفاده کنید:\n"
        txt += "\n".join([f"• قفل {k}" for k in LOCK_MAP.keys()])
        bot.edit_message_text(txt, call.message.chat.id, call.message.id, parse_mode="HTML")

    elif call.data == "panel_welcome":
        w = data["welcome"].get(gid, {"enabled": True})
        status = "✅ روشن" if w.get("enabled", True) else "🚫 خاموش"
        bot.edit_message_text(f"🎉 خوشامد: {status}\n"
                              "➕ «تنظیم خوشامد» برای تغییر متن یا عکس استفاده کنید.\n"
                              "💡 از دستورات: خوشامد روشن / خوشامد خاموش", 
                              call.message.chat.id, call.message.id)

    elif call.data == "panel_stats":
        bot.edit_message_text("📊 برای دیدن آمار روزانه بنویسید:\n`آمار`", 
                              call.message.chat.id, call.message.id, parse_mode="Markdown")

    elif call.data == "panel_fun":
        bot.edit_message_text("😂 <b>مدیریت جوک و فال</b>\n"
                              "➕ ثبت جوک / ثبت فال با ریپلای انجام می‌شود.\n"
                              "📜 لیست جوک‌ها / فال‌ها را ببینید.\n"
                              "🗑 حذف جوک ۲ / حذف فال ۳", 
                              call.message.chat.id, call.message.id, parse_mode="HTML")

    elif call.data == "panel_clear":
        bot.edit_message_text("🧹 برای پاکسازی:\n• پاکسازی (حذف ۱۰۰ پیام آخر)\n• حذف ۲۰ (عدد دلخواه)", 
                              call.message.chat.id, call.message.id)

    elif call.data == "panel_broadcast":
        bot.edit_message_text("📢 ارسال همگانی:\nپیامت را ریپلای کن و بنویس «ارسال»", 
                              call.message.chat.id, call.message.id)

# ================= 👋 خوشامد =================
@bot.message_handler(content_types=["new_chat_members"])
def welcome(m):
    data = load_data(); gid = str(m.chat.id)
    s = data["welcome"].get(gid, {"enabled": True, "type": "text", "content": None, "file_id": None})
    if not s.get("enabled", True): return
    user = m.new_chat_members[0]
    name = user.first_name or "دوست جدید"
    t = shamsi_time()
    text = s.get("content") or f"سلام {name} 🌙\nبه گروه {m.chat.title} خوش اومدی 😎\n⏰ {t}"
    text = text.replace("{name}", name).replace("{time}", t)
    if s.get("file_id"):
        bot.send_photo(m.chat.id, s["file_id"], caption=text)
    else:
        bot.send_message(m.chat.id, text)

@bot.message_handler(func=lambda m: cmd_text(m) == "تنظیم خوشامد" and m.reply_to_message)
def set_welcome(m):
    if not is_admin(m.chat.id, m.from_user.id): return
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

@bot.message_handler(func=lambda m: cmd_text(m) in ["خوشامد روشن", "خوشامد خاموش"])
def toggle_welcome(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    data = load_data(); gid = str(m.chat.id)
    en = cmd_text(m) == "خوشامد روشن"
    data["welcome"].setdefault(gid, {"enabled": True})
    data["welcome"][gid]["enabled"] = en
    save_data(data)
    bot.reply_to(m, "✅ خوشامد روشن شد" if en else "🚫 خوشامد خاموش شد")

# ================= 🚫 بن / سکوت / اخطار =================
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "بن")
def ban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    if is_sudo(uid): return bot.reply_to(m, "⚡ نمی‌توان سودو را بن کرد.")
    try:
        bot.ban_chat_member(m.chat.id, uid)
        bot.reply_to(m, f"🚫 کاربر {uid} بن شد.")
    except:
        bot.reply_to(m, "❗ خطا در انجام عملیات بن.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "اخطار")
def warn_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = str(m.reply_to_message.from_user.id)
    gid = str(m.chat.id)
    data = load_data()
    data["warns"].setdefault(gid, {})
    data["warns"][gid][uid] = data["warns"][gid].get(uid, 0) + 1
    count = data["warns"][gid][uid]
    save_data(data)
    if count >= 3:
        try:
            bot.ban_chat_member(m.chat.id, int(uid))
            bot.reply_to(m, f"🚫 کاربر {uid} به دلیل ۳ اخطار بن شد.")
            data["warns"][gid][uid] = 0
            save_data(data)
        except:
            bot.reply_to(m, "❗ خطا در بن کاربر.")
    else:
        bot.reply_to(m, f"⚠️ کاربر {uid} اخطار {count}/3 دریافت کرد.")

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

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "لیست جوک‌ها")
def list_jokes(m):
    data = load_data(); jokes = data.get("jokes", [])
    if not jokes: return bot.reply_to(m, "❗ جوکی ثبت نشده.")
    txt = "\n".join([f"{i+1}. {t}" for i, t in enumerate(jokes)])
    bot.reply_to(m, "📜 لیست جوک‌ها:\n" + txt)

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("حذف جوک "))
def del_joke(m):
    data = load_data(); jokes = data.get("jokes", [])
    try:
        idx = int(cmd_text(m).split()[2]) - 1
        jokes.pop(idx)
        data["jokes"] = jokes
        save_data(data)
        bot.reply_to(m, "🗑 جوک حذف شد.")
    except:
        bot.reply_to(m, "❗ شماره جوک نامعتبر است.")

# ==== فال ====
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

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "لیست فال‌ها")
def list_fals(m):
    data = load_data(); falls = data.get("falls", [])
    if not falls: return bot.reply_to(m, "❗ فالی ثبت نشده.")
    txt = "\n".join([f"{i+1}. {t}" for i, t in enumerate(falls)])
    bot.reply_to(m, "📜 لیست فال‌ها:\n" + txt)

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("حذف فال "))
def del_fal(m):
    data = load_data(); falls = data.get("falls", [])
    try:
        idx = int(cmd_text(m).split()[2]) - 1
        falls.pop(idx)
        data["falls"] = falls
        save_data(data)
        bot.reply_to(m, "🗑 فال حذف شد.")
    except:
        bot.reply_to(m, "❗ شماره فال نامعتبر است.")

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
            if msg.text:
                bot.send_message(uid, msg.text)
            elif msg.photo:
                bot.send_photo(uid, msg.photo[-1].file_id, caption=msg.caption or "")
            total += 1
        except:
            continue
    bot.reply_to(m, f"📢 پیام به {total} کاربر ارسال شد.")

# ================= 🧹 پاکسازی =================
@bot.message_handler(func=lambda m: cmd_text(m) == "پاکسازی")
def clear_recent(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    for i in range(100):
        try: bot.delete_message(m.chat.id, m.message_id - i)
        except: continue
    bot.send_message(m.chat.id, "🧼 ۱۰۰ پیام اخیر پاک شد.", disable_notification=True)

@bot.message_handler(func=lambda m: cmd_text(m).startswith("حذف "))
def delete_messages(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        count = int(cmd_text(m).split()[1])
        for i in range(count):
            bot.delete_message(m.chat.id, m.message_id - i)
        bot.send_message(m.chat.id, f"🧹 {count} پیام حذف شد.", disable_notification=True)
    except:
        bot.reply_to(m, "❗ فرمت نادرست. مثل: حذف 20")

# ================= 👑 پاسخ به سودو =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).lower() in ["سلام","ربات","bot"])
def sudo_reply(m):
    bot.reply_to(m, f"سلام 👑 {m.from_user.first_name}!\nدر خدمتتم سودوی عزیز 🤖")

# ================= 🚀 اجرای نهایی =================
print("🤖 ربات مدیریتی v11.4 UltraPanel فعال شد!")
bot.infinity_polling(timeout=60, long_polling_timeout=30)
