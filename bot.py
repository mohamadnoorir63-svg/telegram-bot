# -*- coding: utf-8 -*-
# Persian Lux AI Panel – Heroku Edition

import os, json, random, time, logging
import jdatetime
import telebot
from telebot import types
from openai import OpenAI

# ================= ⚙️ تنظیمات پایه =================
TOKEN   = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
client = OpenAI(api_key=OPENAI_KEY)

DATA_FILE = "data.json"
LOG_FILE  = "error.log"

logging.basicConfig(filename=LOG_FILE, level=logging.ERROR,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# ================= 💾 فایل داده =================
def base_data():
    return {
        "welcome": {}, "locks": {}, "admins": {}, "sudo_list": [],
        "banned": {}, "muted": {}, "warns": {}, "users": [],
        "ai_status": True, "charges": {},
        "jokes": [], "falls": []
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

# ================= ابزارها =================
def shamsi_date(): return jdatetime.datetime.now().strftime("%A %d %B %Y")
def shamsi_time(): return jdatetime.datetime.now().strftime("%H:%M:%S")
def cmd_text(m): return (getattr(m, "text", None) or "").strip()

def is_sudo(uid):
    d = load_data()
    return str(uid) in [str(SUDO_ID)] + d.get("sudo_list", [])

def is_admin(chat_id, uid):
    d = load_data(); gid = str(chat_id)
    if is_sudo(uid): return True
    if str(uid) in d["admins"].get(gid, []): return True
    try:
        st = bot.get_chat_member(chat_id, uid).status
        return st in ("administrator", "creator")
    except: return False# ================= 💬 کنترل هوش مصنوعی و شارژ =================
def get_charge(uid):
    d = load_data()
    return d["charges"].get(str(uid), 5)

def reduce_charge(uid):
    d = load_data()
    uid = str(uid)
    if uid not in d["charges"]:
        d["charges"][uid] = 5
    if d["charges"][uid] > 0:
        d["charges"][uid] -= 1
    save_data(d)

def add_charge(uid, amount):
    d = load_data()
    uid = str(uid)
    d["charges"][uid] = d["charges"].get(uid, 0) + amount
    save_data(d)

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and m.reply_to_message and cmd_text(m).startswith("شارژ "))
def charge_user(m):
    try:
        amount = int(cmd_text(m).split(" ")[1])
        uid = m.reply_to_message.from_user.id
        add_charge(uid, amount)
        bot.reply_to(m, f"💎 به کاربر <a href='tg://user?id={uid}'>شارژ {amount}</a> اضافه شد.")
    except:
        bot.reply_to(m, "⚠️ فرمت نادرست. مثال: شارژ ۵ (در پاسخ به کاربر)")

@bot.message_handler(func=lambda m: cmd_text(m) in ["ربات جواب بده", "ربات روشن"])
def ai_on(m):
    d = load_data(); d["ai_status"] = True; save_data(d)
    bot.reply_to(m, "🤖 ربات هوشمند فعال شد و آماده پاسخ‌گویی است!")

@bot.message_handler(func=lambda m: cmd_text(m) in ["ربات خاموش", "ربات توقف"])
def ai_off(m):
    d = load_data(); d["ai_status"] = False; save_data(d)
    bot.reply_to(m, "🔕 ربات خاموش شد و دیگر پاسخ نمی‌دهد.")

# ================= 🧠 پاسخ هوشمند از ChatGPT =================
@bot.message_handler(func=lambda m: m.text and not m.text.startswith("/"))
def ai_reply(m):
    d = load_data()
    if not d.get("ai_status", True):
        return
    uid = str(m.from_user.id)
    if not is_sudo(uid):
        if get_charge(uid) <= 0:
            return bot.reply_to(m, "⚠️ شارژ شما تمام شده است.\nبرای تمدید با پشتیبانی @NOORI_NOOR تماس بگیرید.")
        reduce_charge(uid)
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful Persian assistant."},
                {"role": "user", "content": m.text}
            ]
        )
        bot.reply_to(m, response.choices[0].message.content)
    except Exception as e:
        logging.error(f"AI error: {e}")
        bot.reply_to(m, "❗ خطا در ارتباط با هوش مصنوعی، بعداً تلاش کن.")

# ================= 🎭 جوک و فال =================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "ثبت جوک")
def add_joke(m):
    d = load_data()
    txt = (m.reply_to_message.text or "").strip()
    if not txt:
        return bot.reply_to(m, "⚠️ لطفاً روی پیام متنی ریپلای کن تا ذخیره کنم.")
    d["jokes"].append(txt); save_data(d)
    bot.reply_to(m, f"😂 جوک ذخیره شد:\n{txt}")

@bot.message_handler(func=lambda m: cmd_text(m) == "جوک")
def random_joke(m):
    d = load_data(); jokes = d.get("jokes", [])
    if not jokes: return bot.reply_to(m, "😅 هنوز جوکی ثبت نشده!")
    bot.reply_to(m, f"😂 {random.choice(jokes)}")

@bot.message_handler(func=lambda m: cmd_text(m) == "فال")
def random_fal(m):
    d = load_data(); f = d.get("falls", [])
    if not f: return bot.reply_to(m, "😅 هنوز هیچ فالی ثبت نشده!")
    bot.reply_to(m, f"🔮 فال امروز:\n{random.choice(f)}")

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
    bot.send_message(m.chat.id, text)

# ================= 🔒 قفل‌ها =================
LOCK_MAP = {"لینک":"link","گروه":"group","عکس":"photo","ویدیو":"video","استیکر":"sticker","گیف":"gif"}

@bot.message_handler(func=lambda m: cmd_text(m).startswith("قفل ") or cmd_text(m).startswith("بازکردن "))
def toggle_lock(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    d = load_data(); gid = str(m.chat.id)
    part = cmd_text(m).split(" ")
    if len(part) < 2: return
    key_fa = part[1]; lock_type = LOCK_MAP.get(key_fa)
    if not lock_type: return bot.reply_to(m, "❌ نوع قفل نامعتبر است.")
    en = cmd_text(m).startswith("قفل ")
    d["locks"].setdefault(gid, {k: False for k in LOCK_MAP.values()})
    d["locks"][gid][lock_type] = en; save_data(d)
    bot.reply_to(m, f"{'🔒' if en else '🔓'} قفل {key_fa} {'فعال' if en else 'غیرفعال'} شد.")

# ================= ℹ️ راهنما =================
@bot.message_handler(func=lambda m: cmd_text(m) == "راهنما")
def show_help(m):
    txt = (
        "📘 <b>راهنمای Persian Lux AI Panel</b>\n\n"
        "🧠 ربات جواب بده / ربات خاموش\n"
        "⚡ شارژ کاربر (در ریپلای → شارژ ۵)\n"
        "😂 جوک / ثبت جوک / فال / ثبت فال\n"
        "🔒 قفل لینک / بازکردن لینک\n"
        "👋 خوشامد روشن / خاموش\n\n"
        "👑 سازنده: محمد نوری | @NOORI_NOOR"
    )
    bot.reply_to(m, txt)

# ================= 🚀 اجرای نهایی =================
@bot.message_handler(commands=["start"])
def start_cmd(m):
    d = load_data()
    uid = str(m.from_user.id)
    if uid not in d["users"]:
        d["users"].append(uid)
        save_data(d)
    bot.send_message(m.chat.id,
        "👋 سلام! من ربات <b>Persian Lux AI Panel</b> هستم.\n🤖 آماده‌ام تا با هوش مصنوعی گفتگو کنم و گروهت رو مدیریت کنم.")

print("🤖 Persian Lux AI Panel در حال اجراست...")
while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        logging.error(f"polling crash: {e}")
        time.sleep(5)
