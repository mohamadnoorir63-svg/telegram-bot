# -*- coding: utf-8 -*-
# Persian Lux Panel V15 – Full Rewrite (Updated Stats + Fal)
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
        "welcome": {}, "locks": {}, "admins": {}, "sudo_list": [],
        "banned": {}, "muted": {}, "warns": {}, "users": [],
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

# ================= 🧩 ابزارها =================
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
    except: return False

# ================= 🆔 آیدی لوکس =================
@bot.message_handler(func=lambda m: cmd_text(m) in ["آیدی","ایدی"])
def show_id(m):
    try:
        user = m.from_user
        name = user.first_name or ""
        uid = user.id
        caption = (
            f"🧾 <b>مشخصات کاربر</b>\n"
            f"👤 نام: {name}\n"
            f"🆔 آیدی عددی: <code>{uid}</code>\n"
            f"💬 آیدی گروه: <code>{m.chat.id}</code>\n"
            f"📅 تاریخ: {shamsi_date()}\n"
            f"⏰ ساعت: {shamsi_time()}"
        )
        photos = bot.get_user_profile_photos(uid)
        if photos.total_count > 0:
            file_id = photos.photos[0][-1].file_id
            bot.send_photo(m.chat.id, file_id, caption=caption)
        else:
            bot.reply_to(m, caption)
    except Exception as e:
        logging.error(f"show_id error: {e}")
        bot.reply_to(m, f"🆔 <code>{m.from_user.id}</code>\n⏰ {shamsi_time()}")# ================= 📊 آمار پیشرفته و واقعی =================
from collections import defaultdict

STATS_FILE = "stats.json"

def base_stats():
    return {"messages": 0, "photos": 0, "videos": 0, "voices": 0, "stickers": 0, "gifs": 0, "links": 0, "forwards": 0, "users": defaultdict(int)}

def load_stats():
    if not os.path.exists(STATS_FILE):
        save_stats(base_stats())
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return base_stats()

def save_stats(d):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

# ثبت فعالیت‌ها
@bot.message_handler(content_types=["text", "photo", "video", "voice", "sticker", "animation", "document"])
def track_stats(m):
    stats = load_stats()
    uid = str(m.from_user.id)
    stats["messages"] += 1
    stats["users"][uid] = stats["users"].get(uid, 0) + 1
    if "t.me/" in (m.text or ""): stats["links"] += 1
    if m.forward_from or m.forward_from_chat: stats["forwards"] += 1
    if m.photo: stats["photos"] += 1
    if m.video: stats["videos"] += 1
    if m.voice: stats["voices"] += 1
    if m.sticker: stats["stickers"] += 1
    if m.animation: stats["gifs"] += 1
    save_stats(stats)

@bot.message_handler(func=lambda m: cmd_text(m) in ["آمار","آمار روزانه"])
def show_stats(m):
    stats = load_stats()
    total_msgs = stats.get("messages", 0)
    photos = stats.get("photos", 0)
    videos = stats.get("videos", 0)
    voices = stats.get("voices", 0)
    gifs = stats.get("gifs", 0)
    stickers = stats.get("stickers", 0)
    links = stats.get("links", 0)
    forwards = stats.get("forwards", 0)
    users = stats.get("users", {})

    if users:
        top_user_id = max(users, key=users.get)
        top_user_msgs = users[top_user_id]
        top_user = f"<a href='tg://user?id={top_user_id}'>کاربر {top_user_id}</a> ({top_user_msgs} پیام)"
    else:
        top_user = "هیچ فعالیتی ثبت نشده است."

    bot.reply_to(m, f"""
♡ <b>فعالیت‌های امروز تا این لحظه:</b>

📅 تاریخ: {shamsi_date()}
⏰ ساعت: {shamsi_time()}

✛ کل پیام‌ها: {total_msgs}
✛ عکس‌ها: {photos}
✛ ویدیوها: {videos}
✛ ویس‌ها: {voices}
✛ گیف‌ها: {gifs}
✛ استیکرها: {stickers}
✛ لینک‌ها: {links}
✛ پیام‌های فورواردی: {forwards}

🏆 فعال‌ترین عضو:
{top_user}
""", disable_web_page_preview=True)


# ================= 🔮 فال جدید (چند‌دسته‌ای و تصادفی) =================
FAL_CATEGORIES = {
    "عاشقانه": [
        "💞 عشقت امروز از تو خبری می‌گیرد!",
        "💌 دل کسی برایت تنگ شده است.",
        "💘 اتفاقی عاشقانه در راه است!",
        "💋 امروز کسی در خفا به تو فکر می‌کند..."
    ],
    "کاری": [
        "💼 روزی پر از انرژی در کار در پیش داری.",
        "📈 تلاشت نتیجه می‌دهد، ادامه بده!",
        "💡 یک فرصت شغلی در انتظارت است.",
        "🏆 موفقیت از آن توست!"
    ],
    "روزانه": [
        "☀️ روزی آرام و پر از انرژی مثبت در پیش داری.",
        "🌈 امروز اتفاق کوچکی لبخندت را می‌سازد.",
        "🍀 به اتفاقات اطراف دقت کن، نشانه‌ای در راه است.",
        "🌻 آرامش را در چیزهای ساده پیدا کن."
    ],
    "طنز": [
        "😂 امروز حسابی می‌خندی!",
        "🤣 مواظب باش زیادی شوخی نکنی 😅",
        "😜 یه نفر قراره تو رو سر کار بذاره، مراقب باش!",
        "😆 خنده بر هر درد بی‌درمان دواست، پس بخند!"
    ],
    "عمومی": [
        "✨ مسیرت روشن است، فقط ادامه بده.",
        "💫 آرام باش، همه‌چیز درست می‌شود.",
        "🌙 چیزی که دنبالش هستی، به‌زودی می‌رسد.",
        "🌹 دلت پاک است، روزهای قشنگی در راهند."
    ]
}

@bot.message_handler(func=lambda m: cmd_text(m) == "فال")
def random_fal(m):
    cat = random.choice(list(FAL_CATEGORIES.keys()))
    text = random.choice(FAL_CATEGORIES[cat])
    bot.reply_to(m, f"🔮 <b>فال امروز ({cat})</b>\n{text}")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("فال "))
def fal_by_category(m):
    part = cmd_text(m).split(" ", 1)
    if len(part) < 2:
        return bot.reply_to(m, "📚 دسته فال را بنویس (مثلاً فال عاشقانه)")
    cat = part[1].strip()
    if cat not in FAL_CATEGORIES:
        return bot.reply_to(m, "❌ دسته‌ای با این نام وجود ندارد.\nدسته‌ها: عاشقانه | کاری | روزانه | طنز | عمومی")
    text = random.choice(FAL_CATEGORIES[cat])
    bot.reply_to(m, f"🔮 <b>فال {cat}</b>\n{text}")

@bot.message_handler(func=lambda m: cmd_text(m) == "دسته فال‌ها")
def list_fal_categories(m):
    cats = " | ".join(FAL_CATEGORIES.keys())
    bot.reply_to(m, f"📚 دسته‌های موجود فال:\n<code>{cats}</code>\n\nبرای مثال بنویس:\nفال عاشقانه")# ================= 😂 جوک =================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "ثبت جوک")
def add_joke(m):
    d = load_data()
    txt = (m.reply_to_message.text or "").strip()
    if not txt:
        return bot.reply_to(m, "⚠️ لطفاً روی پیام متنی ریپلای کن تا ذخیره کنم.")
    if txt in d["jokes"]:
        return bot.reply_to(m, "⚠️ این جوک قبلاً ثبت شده بود.")
    d["jokes"].append(txt)
    save_data(d)
    bot.reply_to(m, f"😂 جوک جدید ذخیره شد:\n\n«{txt[:60]}...»")

@bot.message_handler(func=lambda m: cmd_text(m) == "جوک")
def random_joke(m):
    d = load_data()
    jokes = d.get("jokes", [])
    if not jokes:
        return bot.reply_to(m, "😅 هنوز جوکی ثبت نشده!\nبا دستور «ثبت جوک» اضافه کن.")
    bot.reply_to(m, f"😂 <b>جوک امروز:</b>\n{random.choice(jokes)}")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست جوک")
def list_jokes(m):
    d = load_data()
    jokes = d.get("jokes", [])
    if not jokes:
        return bot.reply_to(m, "❗ هیچ جوکی ثبت نشده.")
    text = "\n".join([f"{i+1}. {j}" for i, j in enumerate(jokes)])
    bot.reply_to(m, f"📜 <b>لیست جوک‌ها:</b>\n{text}")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("حذف جوک "))
def del_joke(m):
    d = load_data()
    jokes = d.get("jokes", [])
    try:
        parts = cmd_text(m).split()
        if len(parts) < 3:
            return bot.reply_to(m, "⚠️ فرمت درست دستور: حذف جوک 1")
        idx = int(parts[2]) - 1
        if idx < 0 or idx >= len(jokes): raise ValueError
        removed = jokes.pop(idx)
        save_data(d)
        bot.reply_to(m, f"🗑 جوک شماره {idx+1} حذف شد:\n«{removed}»")
    except:
        bot.reply_to(m, "❗ شماره‌ی جوک نامعتبر است یا خطایی رخ داده.")

# ================= 🧹 حذف پیام‌ها =================
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

# ================= 📢 ارسال همگانی =================
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
        except:
            continue
    bot.reply_to(m, f"📢 پیام برای {total} کاربر ارسال شد.")

# ================= ℹ️ راهنما =================
@bot.message_handler(func=lambda m: cmd_text(m) == "راهنما")
def show_help(m):
    txt = (
        "📘 <b>راهنمای Persian Lux Panel V15 (Updated Stats + Fal)</b>\n\n"
        "🆔 آیدی لوکس | ساعت | لینک ربات/گروه\n"
        "📊 آمار پیشرفته (پیام، عکس، ویدیو، لینک...)\n"
        "👋 خوشامد: تنظیم | روشن/خاموش\n"
        "🔒 قفل‌ها: لینک | عکس | فیلم | گیف | گروه\n"
        "🚫 بن | 🔇 سکوت | ⚠️ اخطار (۳=اخراج)\n"
        "😂 جوک‌ها: ثبت جوک | لیست جوک | حذف جوک N\n"
        "🔮 فال‌ها: فال | فال عاشقانه | دسته فال‌ها\n"
        "🧹 حذف N پیام | 📢 ارسال همگانی (فقط سودو)\n\n"
        "👑 توسعه و طراحی: محمد | Persian Lux Panel"
    )
    bot.reply_to(m, txt)

# ================= 🤖 پاسخ سودو =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).lower() in ["سلام","ربات","هی","bot"])
def sudo_reply(m):
    replies = [
        f"👑 جانم {m.from_user.first_name} 💎",
        f"✨ سلام {m.from_user.first_name}! آماده‌ام 💪",
        f"🤖 بله {m.from_user.first_name}، در خدمتتم 🔥"
    ]
    bot.reply_to(m, random.choice(replies))

# ================= 🚀 اجرای نهایی =================
@bot.message_handler(commands=["start"])
def start_cmd(m):
    d = load_data()
    uid = str(m.from_user.id)
    if uid not in d["users"]:
        d["users"].append(uid)
        save_data(d)
    bot.reply_to(m, "👋 سلام! ربات مدیریتی Persian Lux Panel فعال است.\nبرای راهنما بنویس: «راهنما»")

print("🤖 Persian Lux Panel V15 (Stats + Fal Updated) در حال اجراست...")
while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        logging.error(f"polling crash: {e}")
        time.sleep(5)
