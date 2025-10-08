# -*- coding: utf-8 -*-
# Persian Lux Panel V15 – Full Rewrite (Stats + Fal Updated)
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
STATS_FILE = "stats.json"
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
        bot.reply_to(m, f"🆔 <code>{m.from_user.id}</code>\n⏰ {shamsi_time()}")

# ================= 🕒 آمار پیشرفته جدید =================
def base_stats():
    return {
        "messages": 0, "photos": 0, "videos": 0, "voices": 0,
        "stickers": 0, "gifs": 0, "links": 0, "forwards": 0, "users": {}
    }

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

@bot.message_handler(content_types=["text", "photo", "video", "voice", "sticker", "animation"])
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

@bot.message_handler(func=lambda m: cmd_text(m) == "آمار")
def show_stats(m):
    stats = load_stats()
    total = stats["messages"]
    photos = stats["photos"]
    videos = stats["videos"]
    voices = stats["voices"]
    stickers = stats["stickers"]
    gifs = stats["gifs"]
    links = stats["links"]
    forwards = stats["forwards"]

    users = stats.get("users", {})
    if users:
        top_user_id = max(users, key=users.get)
        top_count = users[top_user_id]
        top_user = f"<a href='tg://user?id={top_user_id}'>کاربر {top_user_id}</a> ({top_count} پیام)"
    else:
        top_user = "❗ هنوز فعالیتی ثبت نشده است."

    bot.reply_to(m, f"""
📊 <b>آمار دقیق ربات Persian Lux Panel</b>

📅 تاریخ: {shamsi_date()}
⏰ ساعت: {shamsi_time()}

💬 کل پیام‌ها: {total}
🖼 عکس‌ها: {photos}
🎥 ویدیوها: {videos}
🎙 ویس‌ها: {voices}
🎭 استیکرها: {stickers}
🎞 گیف‌ها: {gifs}
🔗 لینک‌ها: {links}
📤 پیام‌های فورواردی: {forwards}

🏆 فعال‌ترین کاربر:
{top_user}
""", disable_web_page_preview=True)# ================= 🔮 فال جدید چنددسته‌ای =================
FAL_CATEGORIES = {
    "عاشقانه": [
        "💞 عشقت امروز به تو فکر می‌کند!",
        "💌 دلتنگی در راه است، تماس بگیر!",
        "💘 احساسات تازه‌ای در قلبت شکل می‌گیرد.",
        "💋 نگاهت امروز جادوی خاصی دارد!"
    ],
    "کاری": [
        "💼 روز پرباری در کار خواهی داشت.",
        "📈 موفقیت نزدیک است، تسلیم نشو.",
        "💡 فرصت خوبی برای پیشرفت در کارت داری.",
        "🏆 تلاش امروزت نتیجه می‌دهد."
    ],
    "روزانه": [
        "☀️ امروز لبخند بزن، جهان لبخندت را می‌خواهد.",
        "🌈 اتفاقی کوچک شادی بزرگی می‌آورد.",
        "🍀 نشانه‌های خوبی در اطرافت هست، دقت کن.",
        "🌻 با آرامش، همه‌چیز درست می‌شود."
    ],
    "طنز": [
        "🤣 قراره حسابی بخندی، آماده باش!",
        "😜 شوخی امروزت از کنترل خارج می‌شه!",
        "😂 امروز کسی با شوخی‌اش غافلگیرت می‌کنه!",
        "😆 خنده، بهترین داروی توئه امروز!"
    ],
    "عمومی": [
        "✨ انرژی مثبت اطرافت رو بغل کن.",
        "🌙 آرزوهای قشنگت در راهن، صبور باش.",
        "🌹 اتفاق خوبی در سکوت در حال رخ دادنه.",
        "💫 فقط ادامه بده، مسیر درسته."
    ]
}

@bot.message_handler(func=lambda m: cmd_text(m) == "فال")
def random_fal(m):
    cat = random.choice(list(FAL_CATEGORIES.keys()))
    fal_text = random.choice(FAL_CATEGORIES[cat])
    bot.reply_to(m, f"🔮 <b>فال امروز ({cat})</b>\n{fal_text}")

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
    bot.reply_to(m, f"📚 دسته‌های موجود فال:\n<code>{cats}</code>\n\nبرای مثال بنویس:\nفال عاشقانه")

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

# ================= بقیه دستورات بدون تغییر =================

@bot.message_handler(func=lambda m: cmd_text(m) == "راهنما")
def show_help(m):
    txt = (
        "📘 <b>راهنمای Persian Lux Panel V15 (Fal + Stats Updated)</b>\n\n"
        "🆔 آیدی لوکس | ساعت | لینک ربات/گروه\n"
        "📊 آمار دقیق + فعال‌ترین کاربر\n"
        "🔮 فال‌ها: فال | فال عاشقانه | دسته فال‌ها\n"
        "😂 جوک‌ها | خوشامد | قفل‌ها | اخطار | سکوت | بن\n"
        "🧹 حذف پیام‌ها | 📢 ارسال همگانی\n\n"
        "👑 توسعه‌دهنده: محمد | Persian Lux Panel"
    )
    bot.reply_to(m, txt)

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

print("🤖 Persian Lux Panel V15 (Fal + Stats Updated) در حال اجراست...")
while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        logging.error(f"polling crash: {e}")
        time.sleep(5)
