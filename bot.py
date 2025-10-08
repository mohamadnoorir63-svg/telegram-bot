# -*- coding: utf-8 -*-
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

# ================= 📂 داده‌ها =================
def base_data():
    return {
        "welcome": {}, "locks": {}, "admins": {}, "sudo_list": [],
        "banned": {}, "muted": {}, "warns": {}, "jokes": [], "falls": [],
        "users": []
    }

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(base_data())
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = base_data(); save_data(data)
    for k in base_data():
        if k not in data: data[k] = base_data()[k]
    save_data(data)
    return data

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def register_group(gid):
    d = load_data(); gid = str(gid)
    d["welcome"].setdefault(gid, {"enabled": True, "type": "text", "content": None, "file_id": None})
    d["locks"].setdefault(gid, {k: False for k in ["link","group","photo","video","sticker","gif","file","music","voice","forward"]})
    save_data(d)

# ================= 🕒 زمان و ابزارها =================
def cmd_text(m): return (getattr(m, "text", None) or "").strip()
def now_teh(): return datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
def shamsi_date(): return jdatetime.datetime.now().strftime("%A %d %B %Y")
def shamsi_time(): return jdatetime.datetime.now().strftime("%H:%M:%S")

def is_sudo(uid):
    d = load_data()
    return str(uid) in [str(SUDO_ID)] + [str(x) for x in d.get("sudo_list", [])]

def is_admin(chat_id, uid):
    d = load_data(); gid = str(chat_id)
    if is_sudo(uid): return True
    if str(uid) in d["admins"].get(gid, []): return True
    try:
        st = bot.get_chat_member(chat_id, uid).status
        return st in ("administrator", "creator")
    except: return False

# ================= 👋 خوشامد =================
@bot.message_handler(content_types=["new_chat_members"])
def welcome(m):
    register_group(m.chat.id)
    d = load_data(); gid = str(m.chat.id)
    s = d["welcome"].get(gid, {"enabled": True})
    if not s.get("enabled", True): return
    user = m.new_chat_members[0]
    name = user.first_name or "دوست جدید"
    text = s.get("content") or f"سلام {name} 🌸\nبه {m.chat.title} خوش اومدی 🌹\n⏰ {shamsi_time()}"
    text = text.replace("{name}", name).replace("{time}", shamsi_time())
    if s.get("file_id"):
        bot.send_photo(m.chat.id, s["file_id"], caption=text)
    else:
        bot.send_message(m.chat.id, text)

@bot.message_handler(func=lambda m: cmd_text(m) == "تنظیم خوشامد" and m.reply_to_message)
def set_welcome(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    d = load_data(); gid = str(m.chat.id)
    msg = m.reply_to_message
    if msg.photo:
        d["welcome"][gid] = {"enabled": True, "type": "photo", "file_id": msg.photo[-1].file_id, "content": msg.caption or ""}
    elif msg.text:
        d["welcome"][gid] = {"enabled": True, "type": "text", "content": msg.text}
    save_data(d)
    bot.reply_to(m, "✅ پیام خوشامد جدید تنظیم شد.")

@bot.message_handler(func=lambda m: cmd_text(m) in ["خوشامد روشن","خوشامد خاموش"])
def toggle_welcome(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    d = load_data(); gid = str(m.chat.id)
    en = cmd_text(m) == "خوشامد روشن"
    d["welcome"].setdefault(gid, {})["enabled"] = en
    save_data(d)
    bot.reply_to(m, "🟢 خوشامد روشن شد" if en else "🔴 خوشامد خاموش شد")

# ================= 🔒 قفل‌ها =================
LOCK_MAP = {"لینک":"link","گروه":"group","عکس":"photo","ویدیو":"video","استیکر":"sticker","گیف":"gif","فایل":"file","موزیک":"music","ویس":"voice","فوروارد":"forward"}

@bot.message_handler(func=lambda m: cmd_text(m).startswith("قفل ") or cmd_text(m).startswith("بازکردن "))
def toggle_lock(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    d = load_data(); gid = str(m.chat.id)
    part = cmd_text(m).split()
    if len(part) < 2: return
    key = part[1]; lock = LOCK_MAP.get(key)
    if not lock: return bot.reply_to(m, "❌ نوع قفل نامعتبر است.")
    en = cmd_text(m).startswith("قفل ")
    d["locks"].setdefault(gid, {k: False for k in LOCK_MAP.values()})
    if d["locks"][gid][lock] == en: return bot.reply_to(m, "⚠️ از قبل همین وضعیت است.")
    d["locks"][gid][lock] = en; save_data(d)
    if key == "گروه": bot.send_message(m.chat.id, "🔒 گروه بسته شد." if en else "🔓 گروه باز شد.")
    bot.reply_to(m, f"{'🔒' if en else '🔓'} قفل {key} {'فعال' if en else 'غیرفعال'} شد.")

# ================= 😂 جوک و 🔮 فال =================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "ثبت جوک")
def add_joke(m):
    d = load_data(); txt = (m.reply_to_message.text or "").strip()
    if not txt: return bot.reply_to(m, "⚠️ فقط روی پیام متنی ریپلای کن.")
    d["jokes"].append(txt); save_data(d)
    bot.reply_to(m, "😂 جوک ذخیره شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "جوک")
def random_joke(m):
    d = load_data(); j = d.get("jokes", [])
    bot.reply_to(m, random.choice(j) if j else "😅 هنوز جوکی ثبت نشده.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست جوک")
def list_jokes(m):
    d = load_data(); j = d.get("jokes", [])
    if not j: return bot.reply_to(m, "❗ هیچ جوکی ثبت نشده.")
    txt = "\n".join([f"{i+1}. {t}" for i, t in enumerate(j)])
    bot.reply_to(m, f"📜 لیست جوک‌ها:\n{txt}")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("حذف جوک "))
def del_joke(m):
    d = load_data(); j = d.get("jokes", [])
    try:
        n = int(cmd_text(m).split()[2]) - 1
        rm = j.pop(n); save_data(d)
        bot.reply_to(m, f"🗑 جوک حذف شد:\n{rm}")
    except: bot.reply_to(m, "❗ شماره نامعتبر است.")

@bot.message_handler(func=lambda m: cmd_text(m) == "فال")
def random_fal(m):
    d = load_data(); f = d.get("falls", [])
    bot.reply_to(m, random.choice(f) if f else "🔮 هنوز فالی ثبت نشده.")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "ثبت فال")
def add_fal(m):
    d = load_data(); txt = (m.reply_to_message.text or "").strip()
    if not txt: return bot.reply_to(m, "⚠️ فقط روی متن ریپلای کن.")
    d["falls"].append(txt); save_data(d)
    bot.reply_to(m, "🔮 فال ذخیره شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست فال")
def list_fal(m):
    d = load_data(); f = d.get("falls", [])
    if not f: return bot.reply_to(m, "❗ هیچ فالی ثبت نشده.")
    txt = "\n".join([f"{i+1}. {t}" for i,t in enumerate(f)])
    bot.reply_to(m, f"📜 لیست فال‌ها:\n{txt}")

# ================ 🆔 آیدی و ساعت =================
@bot.message_handler(func=lambda m: cmd_text(m) in ["آیدی","ایدی"])
def show_id(m):
    try:
        user = m.from_user
        photos = bot.get_user_profile_photos(user.id, limit=1)
        cap = (f"🧾 <b>نام:</b> {user.first_name}\n🆔 <b>آیدی شما:</b> <code>{user.id}</code>\n"
               f"💬 <b>آیدی گروه:</b> <code>{m.chat.id}</code>\n📅 {shamsi_date()} | ⏰ {shamsi_time()}")
        if photos.total_count > 0:
            bot.send_photo(m.chat.id, photos.photos[0][-1].file_id, caption=cap)
        else:
            bot.reply_to(m, cap)
    except Exception as e:
        logging.error(e)
        bot.reply_to(m, f"🆔 <code>{m.from_user.id}</code> | ⏰ {shamsi_time()}")

# ================ 🔗 لینک گروه و ربات =================
@bot.message_handler(func=lambda m: cmd_text(m) == "لینک گروه")
def group_link(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return bot.reply_to(m, "🔒 فقط مدیران می‌توانند لینک را بگیرند.")
    try:
        link = bot.export_chat_invite_link(m.chat.id)
        bot.reply_to(m, f"🔗 لینک گروه:\n{link}")
    except:
        bot.reply_to(m, "⚠️ مجوز 'Invite Users' را برای ربات فعال کن.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لینک ربات")
def bot_link(m):
    try:
        me = bot.get_me()
        bot.reply_to(m, f"🤖 لینک ربات:\nhttps://t.me/{me.username}")
    except:
        bot.reply_to(m, "❗ خطا در دریافت لینک ربات.")

# ================ 🧭 پنل شیشه‌ای + راهنما =================
@bot.message_handler(func=lambda m: cmd_text(m) in ["پنل","/panel"])
def open_panel(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)):
        return bot.reply_to(m, "🔐 فقط مدیران به پنل دسترسی دارند.")
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🔒 قفل‌ها", callback_data="locks"),
        types.InlineKeyboardButton("👋 خوشامد", callback_data="welcome"),
        types.InlineKeyboardButton("😂 جوک و فال", callback_data="fun"),
        types.InlineKeyboardButton("🚫 مدیریت کاربران", callback_data="manage"),
        types.InlineKeyboardButton("📊 آمار", callback_data="stats"),
        types.InlineKeyboardButton("ℹ️ راهنما", callback_data="help"),
        types.InlineKeyboardButton("❌ بستن پنل", callback_data="close")
    )
    bot.send_message(m.chat.id, "🎛️ <b>پنل مدیریتی لوکس باز شد</b>\nاز دکمه‌ها استفاده کن 👇", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    if call.data == "close":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
    elif call.data == "help":
        txt = (
            "📘 <b>راهنمای Persian Lux Panel V15 Plus</b>\n"
            "• آیدی، ساعت، آمار، لینک گروه/ربات\n"
            "• قفل‌ها، خوشامد، بن/سکوت/اخطار\n"
            "• ثبت و نمایش جوک و فال\n"
            "• حذف عددی و ارسال همگانی\n"
            "👑 توسعه توسط سودو: محمد"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="main"))
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, reply_markup=kb)
    elif call.data == "main":
        open_panel(call.message)

# ================ 🤖 پاسخ سودو =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).lower() in ["سلام","ربات","هی","bot"])
def sudo_reply(m):
    replies = [
        f"👑 جانم {m.from_user.first_name} 💎",
        f"✨ سلام {m.from_user.first_name}! آماده‌ام 💪",
        f"🤖 بله {m.from_user.first_name}، گوش به فرمانم 🔥"
    ]
    bot.reply_to(m, random.choice(replies))

# ================ 🚀 اجرای ربات =================
@bot.message_handler(commands=["start"])
def start_cmd(m):
    d = load_data()
    u = str(m.from_user.id)
    if u not in d["users"]: d["users"].append(u); save_data(d)
    bot.reply_to(m, "👋 سلام!\nمن ربات مدیریتی <b>Persian Lux Panel V15 Plus</b> هستم.\nبرای منوی شیشه‌ای بنویس «پنل» یا /panel")

print("🤖 Persian Lux Panel V15 Plus – Ready!")
while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        logging.error(f"polling crash: {e}")
        time.sleep(5)
