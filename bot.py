# -*- coding: utf-8 -*-
import os, json, random, logging
from datetime import datetime, timedelta
import pytz, jdatetime
import telebot
from telebot import types

# ================= ⚙️ تنظیمات =================
TOKEN = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
DATA_FILE = "data.json"
LOG_FILE = "error.log"

# لاگ برای خطاها
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
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(str(e))

def now_teh():
    return datetime.now(pytz.timezone("Asia/Tehran"))

def shamsi_date():
    return jdatetime.datetime.now().strftime("%A %d %B %Y")

def shamsi_time():
    return jdatetime.datetime.now().strftime("%H:%M:%S")

def register_group(gid):
    data = load_data()
    gid = str(gid)
    data["welcome"].setdefault(gid, {"enabled": True, "type": "text", "content": None, "file_id": None})
    data["locks"].setdefault(gid, {k: False for k in LOCK_MAP.values()})
    if gid not in data["stats"]:
        data["stats"][gid] = {
            "date": str(datetime.now().date()),
            "users": {},
            "counts": {
                "msg":0,"photo":0,"video":0,"voice":0,"music":0,
                "sticker":0,"gif":0,"fwd":0
            }
        }
    save_data(data)

# ================= 🧩 ابزارها =================
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

# ================= 💬 عمومی =================
@bot.message_handler(func=lambda m: cmd_text(m) in ["آیدی","ایدی"])
def cmd_id(m):
    """نمایش آیدی و زمان با عکس"""
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
    if not lock_type: 
        return bot.reply_to(m, "❌ نوع قفل نامعتبر است.")
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

# ================= 🚧 اجرای قفل‌ها و ثبت آمار =================
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
            return bot.delete_message(m.chat.id, m.message_id)
        if locks.get("photo") and m.photo: bot.delete_message(m.chat.id, m.message_id)
        if locks.get("video") and m.video: bot.delete_message(m.chat.id, m.message_id)
        if locks.get("sticker") and m.sticker: bot.delete_message(m.chat.id, m.message_id)
        if locks.get("gif") and m.animation: bot.delete_message(m.chat.id, m.message_id)
        if locks.get("file") and m.document: bot.delete_message(m.chat.id, m.message_id)
        if locks.get("music") and m.audio: bot.delete_message(m.chat.id, m.message_id)
        if locks.get("voice") and m.voice: bot.delete_message(m.chat.id, m.message_id)
        if locks.get("forward") and (m.forward_from or m.forward_from_chat): bot.delete_message(m.chat.id, m.message_id)

        # ✅ ثبت آمار روزانه
        gid = str(m.chat.id)
        uid = str(m.from_user.id)
        d = load_data()
        today = str(datetime.now().date())
        if d["stats"][gid]["date"] != today:
            d["stats"][gid]["date"] = today
            d["stats"][gid]["users"] = {}
            d["stats"][gid]["counts"] = {k:0 for k in d["stats"][gid]["counts"]}
        st = d["stats"][gid]
        st["users"].setdefault(uid, 0)
        st["users"][uid] += 1
        if m.photo: st["counts"]["photo"] += 1
        elif m.video: st["counts"]["video"] += 1
        elif m.voice: st["counts"]["voice"] += 1
        elif m.audio: st["counts"]["music"] += 1
        elif m.sticker: st["counts"]["sticker"] += 1
        elif m.animation: st["counts"]["gif"] += 1
        elif m.forward_from or m.forward_from_chat: st["counts"]["fwd"] += 1
        else: st["counts"]["msg"] += 1
        save_data(d)
    except Exception as e:
        logging.error(f"enforce error: {e}")

# ================= 💬 آمار روزانه =================
@bot.message_handler(func=lambda m: cmd_text(m) == "آمار")
def group_stats(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    d = load_data(); gid = str(m.chat.id)
    register_group(gid)
    st = d["stats"][gid]
    today = shamsi_date(); hour = shamsi_time()
    total = sum(st["counts"].values())
    top_user = None
    if st["users"]:
        top_user_id = max(st["users"], key=st["users"].get)
        try:
            user = bot.get_chat_member(m.chat.id, int(top_user_id)).user.first_name
        except:
            user = f"{top_user_id}"
        top_user = f"• نفر اول🥇 : ({st['users'][top_user_id]} پیام | {user})"
    else:
        top_user = "هیچ فعالیتی ثبت نشده است!"
    msg = f"""♡ فعالیت های امروز تا این لحظه :
➲ تاریخ : {today}
➲ ساعت : {hour}
✛ کل پیام ها : {total}
✛ پیام فورواردی : {st['counts']['fwd']}
✛ فیلم : {st['counts']['video']}
✛ آهنگ : {st['counts']['music']}
✛ ویس : {st['counts']['voice']}
✛ عکس : {st['counts']['photo']}
✛ گیف : {st['counts']['gif']}
✛ استیکر : {st['counts']['sticker']}
✶ فعال ترین اعضای گروه :
{top_user}
✶ کاربران برتر در افزودن عضو :
هیچ فعالیتی ثبت نشده است!
✧ اعضای وارد شده با لینک : ۰
✧ اعضای اد شده : ۰
✧ کل اعضای وارد شده : ۰
✧ اعضای اخراج شده : ۰
✧ اعضای سکوت شده : ۰
✧ اعضای لفت داده : ۰"""
    bot.reply_to(m, msg)# ================= 👋 خوشامد =================
@bot.message_handler(content_types=["new_chat_members"])
def welcome(m):
    register_group(m.chat.id)
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

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف بن")
def unban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    try:
        bot.unban_chat_member(m.chat.id, uid)
        bot.reply_to(m, f"✅ کاربر {uid} از بن خارج شد.")
    except:
        bot.reply_to(m, "❗ خطا در حذف بن کاربر.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "سکوت")
def mute_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    try:
        bot.restrict_chat_member(m.chat.id, uid, can_send_messages=False)
        bot.reply_to(m, f"🤐 کاربر {uid} سکوت شد.")
    except:
        bot.reply_to(m, "❗ خطا در سکوت کاربر.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف سکوت")
def unmute_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    try:
        bot.restrict_chat_member(m.chat.id, uid, can_send_messages=True)
        bot.reply_to(m, f"✅ سکوت کاربر {uid} برداشته شد.")
    except:
        bot.reply_to(m, "❗ خطا در حذف سکوت کاربر.")

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
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ثبت جوک" and m.reply_to_message)
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

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "لیست جوک‌ها")
def list_jokes(m):
    data = load_data(); jokes = data.get("jokes", [])
    if not jokes: return bot.reply_to(m, "❗ جوکی ثبت نشده.")
    txt = "\n".join([f"{i+1}. {t}" for i, t in enumerate(jokes)])
    bot.reply_to(m, "📜 لیست جوک‌ها:\n" + txt)

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).startswith("حذف جوک "))
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

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ثبت فال" and m.reply_to_message)
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

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "لیست فال‌ها")
def list_fals(m):
    data = load_data(); falls = data.get("falls", [])
    if not falls: return bot.reply_to(m, "❗ فالی ثبت نشده.")
    txt = "\n".join([f"{i+1}. {t}" for i, t in enumerate(falls)])
    bot.reply_to(m, "📜 لیست فال‌ها:\n" + txt)

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).startswith("حذف فال "))
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
@bot.message_handler(func=lambda m: cmd_text(m).startswith("حذف "))
def delete_messages(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        count = int(cmd_text(m).split()[1])
        for i in range(count):
            bot.delete_message(m.chat.id, m.message_id - i)
        bot.send_message(m.chat.id, f"🧹 {count} پیام حذف شد.", disable_notification=True)
    except:
        bot.reply_to(m, "❗ خطا در حذف پیام‌ها.")

@bot.message_handler(func=lambda m: cmd_text(m) == "پاکسازی")
def clear_recent(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    for i in range(100):
        try: bot.delete_message(m.chat.id, m.message_id - i)
        except: continue
    bot.send_message(m.chat.id, "🧼 ۱۰۰ پیام اخیر پاک شد.", disable_notification=True)

# ================= 👑 پاسخ ربات به سودو =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).lower() in ["سلام","ربات","bot"])
def sudo_reply(m):
    bot.reply_to(m, f"سلام 👑 {m.from_user.first_name}!\nدر خدمتتم سودوی عزیز 🤖")

# ================= 🚀 اجرای ربات =================
print("🤖 ربات مدیریتی v11 Pro با موفقیت فعال شد!")
bot.infinity_polling(timeout=60, long_polling_timeout=30)
