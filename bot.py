# -*- coding: utf-8 -*-
# Persian Lux Panel V16 Ultimate – Part 1/2
# Designed for Mohammad 👑

import os, json, random, time, logging, requests
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
        "jokes": [], "falls": [], "stats": {}
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

def register_group(gid):
    data = load_data()
    gid = str(gid)
    data["welcome"].setdefault(gid, {"enabled": True, "type": "text", "content": None, "file_id": None})
    data["locks"].setdefault(gid, {k: False for k in ["link","group","photo","video","sticker","gif","file","music","voice","forward"]})
    save_data(data)

# ================= 🧩 ابزارها =================
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
    d = load_data(); gid = str(chat_id)
    if is_sudo(uid): return True
    if str(uid) in d["admins"].get(gid, []): return True
    try:
        st = bot.get_chat_member(chat_id, uid).status
        return st in ("administrator", "creator")
    except: return False

# ================= 🆔 آیدی لوکس =================
@bot.message_handler(func=lambda m: cmd_text(m) in ["آیدی", "ایدی"])
def show_id(m):
    user = m.from_user
    name = user.first_name or ""
    uid = user.id
    profile_photos = bot.get_user_profile_photos(uid)
    caption = (
        f"🧾 <b>مشخصات کاربر:</b>\n"
        f"👤 نام: {name}\n"
        f"🆔 آیدی عددی: <code>{uid}</code>\n"
        f"📅 تاریخ: {shamsi_date()}\n"
        f"⏰ ساعت: {shamsi_time()}"
    )
    if profile_photos.total_count > 0:
        file_id = profile_photos.photos[0][-1].file_id
        bot.send_photo(m.chat.id, file_id, caption=caption)
    else:
        bot.reply_to(m, caption)

# ================= ⏰ ساعت =================
@bot.message_handler(func=lambda m: cmd_text(m) == "ساعت")
def show_time(m):
    bot.reply_to(m, f"⏰ ساعت: {shamsi_time()}\n📅 تاریخ: {shamsi_date()}")

# ================= 🔗 لینک‌ها =================
@bot.message_handler(func=lambda m: cmd_text(m) == "لینک ربات")
def bot_link(m):
    bot.reply_to(m, f"🤖 لینک ربات:\nhttps://t.me/{bot.get_me().username}")

@bot.message_handler(func=lambda m: cmd_text(m) == "لینک گروه")
def group_link(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        link = bot.export_chat_invite_link(m.chat.id)
        bot.reply_to(m, f"🔗 لینک گروه:\n{link}")
    except:
        bot.reply_to(m, "⚠️ دسترسی ساخت لینک ندارم.")

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

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) in ["خوشامد روشن", "خوشامد خاموش"])
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
    key_fa = part[1]; lock_type = LOCK_MAP.get(key_fa)
    if not lock_type: return bot.reply_to(m, "❌ نوع قفل نامعتبر است.")
    en = cmd_text(m).startswith("قفل ")
    d["locks"].setdefault(gid, {k: False for k in LOCK_MAP.values()})
    if d["locks"][gid][lock_type] == en:
        return bot.reply_to(m, "⚠️ این قفل همین حالا هم در همین حالت است.")
    d["locks"][gid][lock_type] = en; save_data(d)

    if lock_type == "group":
        if en:
            bot.send_message(m.chat.id, "🚫 گروه موقتاً بسته شد ❌\n🔒 فقط مدیران می‌توانند پیام ارسال کنند.")
        else:
            bot.send_message(m.chat.id, "✅ گروه باز شد 🌸\n💬 حالا همه می‌تونن گفتگو کنن!")
    else:
        bot.reply_to(m, f"{'🔒' if en else '🔓'} قفل {key_fa} {'فعال' if en else 'غیرفعال'} شد.")# Persian Lux Panel V16 Ultimate – Part 2/2
# ادامه از پارت اول

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
    bot.reply_to(m, f"✅ <a href='tg://user?id={uid}'>کاربر</a> به مدیران افزوده شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست مدیران")
def list_admins(m):
    data = load_data(); gid = str(m.chat.id)
    lst = data["admins"].get(gid, [])
    if not lst: return bot.reply_to(m, "📋 هیچ مدیری ثبت نشده.")
    msg = "👑 لیست مدیران:\n" + "\n".join([f"• <a href='tg://user?id={a}'>کاربر {a}</a>" for a in lst])
    bot.reply_to(m, msg)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "افزودن سودو")
def add_sudo(m):
    if m.from_user.id != SUDO_ID: return
    d = load_data(); uid = str(m.reply_to_message.from_user.id)
    if uid in d["sudo_list"]: return bot.reply_to(m, "⚠️ این کاربر از قبل سودو است.")
    d["sudo_list"].append(uid); save_data(d)
    bot.reply_to(m, f"✅ <a href='tg://user?id={uid}'>کاربر</a> به سودوها افزوده شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست سودو")
def list_sudos(m):
    if not is_sudo(m.from_user.id): return
    d = load_data(); s = d.get("sudo_list", [])
    if not s: return bot.reply_to(m, "❗ هیچ سودویی ثبت نشده.")
    txt = "👑 لیست سودوها:\n" + "\n".join([f"• <a href='tg://user?id={x}'>کاربر {x}</a>" for x in s])
    bot.reply_to(m, txt)

# ================= 🚫 بن / سکوت / اخطار =================
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "بن")
def ban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    if is_sudo(uid): return bot.reply_to(m, "⚡ نمی‌توان سودو را بن کرد.")
    try:
        bot.ban_chat_member(m.chat.id, uid)
        bot.reply_to(m, f"🚫 کاربر <a href='tg://user?id={uid}'>بن</a> شد.")
    except Exception as e:
        bot.reply_to(m, f"❗ خطا در بن کاربر: {e}")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "سکوت")
def mute_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = str(m.reply_to_message.from_user.id)
    d = load_data(); d["muted"][uid] = True; save_data(d)
    bot.reply_to(m, f"🔇 کاربر <a href='tg://user?id={uid}'>ساکت</a> شد.")

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

# ================= 😂 جوک و 🔮 فال =================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "ثبت جوک")
def add_joke(m):
    d = load_data(); txt = (m.reply_to_message.text or "").strip()
    if not txt: return bot.reply_to(m, "⚠️ لطفاً روی پیام متنی ریپلای کن.")
    d["jokes"].append(txt); save_data(d)
    bot.reply_to(m, "😂 جوک ذخیره شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "جوک")
def random_joke(m):
    d = load_data(); jokes = d.get("jokes", [])
    bot.reply_to(m, f"😂 {random.choice(jokes)}" if jokes else "😅 هنوز جوکی ثبت نشده.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست جوک")
def list_jokes(m):
    d = load_data(); jokes = d.get("jokes", [])
    if not jokes: return bot.reply_to(m, "❗ هیچ جوکی ثبت نشده.")
    txt = "\n".join([f"{i+1}. {j}" for i,j in enumerate(jokes)])
    bot.reply_to(m, f"📜 لیست جوک‌ها:\n{txt}")

# ==== فال ====
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "ثبت فال")
def add_fal(m):
    d = load_data(); txt = (m.reply_to_message.text or "").strip()
    if not txt: return bot.reply_to(m, "⚠️ لطفاً روی پیام متنی ریپلای کن.")
    d["falls"].append(txt); save_data(d)
    bot.reply_to(m, "🔮 فال ذخیره شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "فال")
def random_fal(m):
    d = load_data(); f = d.get("falls", [])
    bot.reply_to(m, f"🔮 {random.choice(f)}" if f else "😅 هنوز فالی ثبت نشده.")

# ================= 📊 فعالیت امروز =================
@bot.message_handler(func=lambda m: cmd_text(m) == "فعالیت امروز")
def daily_stats(m):
    d = load_data()
    gid = str(m.chat.id)
    today = datetime.now().strftime("%Y-%m-%d")
    group_stats = d["stats"].get(gid, {}).get(today, {
        "total": 0, "forward": 0, "video": 0, "voice": 0,
        "photo": 0, "sticker": 0, "gif": 0, "audio": 0
    })

    msg = (
        f"♡ فعالیت های امروز تا این لحظه :\n\n"
        f"➲ تاریخ : {shamsi_date()}\n"
        f"➲ ساعت : {shamsi_time()}\n\n"
        f"✛ کل پیام ها : {group_stats['total']}\n"
        f"✛ پیام فورواردی : {group_stats['forward']}\n"
        f"✛ فیلم : {group_stats['video']}\n"
        f"✛ ویس : {group_stats['voice']}\n"
        f"✛ عکس : {group_stats['photo']}\n"
        f"✛ گیف : {group_stats['gif']}\n"
        f"✛ استیکر : {group_stats['sticker']}\n"
        f"✛ آهنگ : {group_stats['audio']}\n"
        f"\n✶ فعال ترین اعضای گروه:\n"
        f"• (در نسخه‌ی بعدی نمایش کاربران فعال اضافه می‌شود)\n\n"
        f"✧ Persian Lux Panel V16 👑"
    )
    bot.reply_to(m, msg)

# شمارش خودکار پیام‌ها
@bot.message_handler(content_types=["text", "photo", "video", "sticker", "voice", "audio", "document"])
def count_messages(m):
    d = load_data(); gid = str(m.chat.id)
    today = datetime.now().strftime("%Y-%m-%d")
    d["stats"].setdefault(gid, {})
    d["stats"][gid].setdefault(today, {
        "total": 0, "forward": 0, "video": 0, "voice": 0,
        "photo": 0, "sticker": 0, "gif": 0, "audio": 0
    })
    s = d["stats"][gid][today]
    s["total"] += 1
    if m.forward_from: s["forward"] += 1
    if m.content_type == "photo": s["photo"] += 1
    if m.content_type == "video": s["video"] += 1
    if m.content_type == "voice": s["voice"] += 1
    if m.content_type == "sticker": s["sticker"] += 1
    if m.content_type == "animation": s["gif"] += 1
    if m.content_type == "audio": s["audio"] += 1
    save_data(d)

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
        except: continue
    bot.reply_to(m, f"📢 پیام برای {total} کاربر ارسال شد.")

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
        d["users"].append(uid); save_data(d)
    bot.reply_to(m, "👋 سلام! ربات مدیریتی Persian Lux Panel V16 فعال است.\nبرای راهنما بنویس: «فعالیت امروز» یا «راهنما»")

print("🤖 Persian Lux Panel V16 Ultimate is running...")
while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        logging.error(f"polling crash: {e}")
        time.sleep(5)
