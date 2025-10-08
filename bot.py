# -*- coding: utf-8 -*-
import os, json, random
from datetime import datetime
import pytz, jdatetime
import telebot
from telebot import types

# ================= ⚙️ تنظیمات =================
TOKEN = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
DATA_FILE = "data.json"

# ================= 🔒 تعریف قفل‌ها =================
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
    for k, v in base_data().items():
        if k not in data:
            data[k] = v
    try:
        save_data(data)
    except:
        pass
    return data

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def now_teh(): return datetime.now(pytz.timezone("Asia/Tehran"))
def shamsi_date(): return jdatetime.datetime.now().strftime("%A %d %B %Y")
def shamsi_time(): return jdatetime.datetime.now().strftime("%H:%M:%S")

def register_group(gid):
    data = load_data()
    gid = str(gid)
    data["welcome"].setdefault(gid, {"enabled": True, "type": "text", "content": None, "file_id": None})
    data["locks"].setdefault(gid, {k: False for k in LOCK_MAP.values()})
    if gid not in data["stats"]:
        data["stats"][gid] = {"date": str(datetime.now().date()), "users": {}, "counts": {
            "msg":0,"photo":0,"video":0,"voice":0,"music":0,"sticker":0,"gif":0,"fwd":0
        }}
    save_data(data)

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
    except: return False

# ================= 💬 عمومی =================
@bot.message_handler(func=lambda m: cmd_text(m) in ["آیدی","ایدی"])
def cmd_id(m):
    user = m.from_user
    try:
        photos = bot.get_user_profile_photos(user.id, limit=1)
        caption = f"🆔 نام: {user.first_name}\n👤 آیدی: <code>{user.id}</code>\n🏠 آیدی گروه: <code>{m.chat.id}</code>\n📅 تاریخ: {shamsi_date()}\n⏰ ساعت: {shamsi_time()}"
        if photos.total_count > 0:
            bot.send_photo(m.chat.id, photos.photos[0][-1].file_id, caption=caption)
        else:
            bot.reply_to(m, caption)
    except:
        bot.reply_to(m, caption)

@bot.message_handler(func=lambda m: cmd_text(m) == "ساعت")
def cmd_time(m):
    bot.reply_to(m, f"⏰ {shamsi_time()}\n📅 {shamsi_date()}")

@bot.message_handler(func=lambda m: cmd_text(m) == "لینک گروه")
def group_link(m):
    try:
        link = bot.export_chat_invite_link(m.chat.id)
        bot.reply_to(m, f"🔗 لینک گروه:\n{link}")
    except:
        bot.reply_to(m, "⚠️ لینک گروه در دسترس نیست. مطمئن شو ربات ادمین با دسترسی Invite هست.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لینک ربات")
def bot_link(m):
    bot.reply_to(m, f"🤖 لینک ربات:\nhttps://t.me/{bot.get_me().username}")

# ================= 🎉 خوشامد =================
@bot.message_handler(content_types=["new_chat_members"])
def welcome(m):
    register_group(m.chat.id)
    data = load_data(); gid = str(m.chat.id)
    s = data["welcome"].get(gid, {"enabled": True})
    if not s.get("enabled", True): return
    user = m.new_chat_members[0]
    name = user.first_name or "دوست جدید"
    t = shamsi_time()
    txt = s.get("content") or f"سلام {name} 🌙\nبه گروه {m.chat.title} خوش اومدی 😎\n⏰ {t}"
    txt = txt.replace("{name}", name).replace("{time}", t)
    if s.get("file_id"):
        bot.send_photo(m.chat.id, s["file_id"], caption=txt)
    else:
        bot.send_message(m.chat.id, txt)

@bot.message_handler(func=lambda m: cmd_text(m) == "تنظیم خوشامد" and m.reply_to_message)
def set_welcome(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    msg = m.reply_to_message; gid = str(m.chat.id)
    data = load_data()
    if msg.photo:
        fid = msg.photo[-1].file_id
        cap = msg.caption or ""
        data["welcome"][gid] = {"enabled": True, "type": "photo", "content": cap, "file_id": fid}
    elif msg.text:
        data["welcome"][gid] = {"enabled": True, "type": "text", "content": msg.text, "file_id": None}
    save_data(data)
    bot.reply_to(m, "✅ پیام خوشامد تنظیم شد.")

@bot.message_handler(func=lambda m: cmd_text(m) in ["خوشامد روشن","خوشامد خاموش"])
def toggle_welcome(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    data = load_data(); gid = str(m.chat.id)
    en = cmd_text(m) == "خوشامد روشن"
    data["welcome"].setdefault(gid, {"enabled": True})
    data["welcome"][gid]["enabled"] = en
    save_data(data)
    bot.reply_to(m, "✅ خوشامد روشن شد" if en else "🚫 خوشامد خاموش شد")

# ================= 🔒 قفل‌ها =================
@bot.message_handler(func=lambda m: cmd_text(m).startswith("قفل ") or cmd_text(m).startswith("بازکردن "))
def toggle_lock(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    data = load_data(); gid = str(m.chat.id)
    part = cmd_text(m).split(" ")
    if len(part) < 2: return
    key_fa = part[1]; lock_type = LOCK_MAP.get(key_fa)
    if not lock_type: return bot.reply_to(m, "❌ نوع قفل نامعتبر است.")
    en = cmd_text(m).startswith("قفل ")
    data["locks"].setdefault(gid, {k: False for k in LOCK_MAP.values()})
    if data["locks"][gid][lock_type] == en:
        return bot.reply_to(m, "⚠️ این مورد از قبل قفل بود." if en else "⚠️ این مورد از قبل باز بود.")
    data["locks"][gid][lock_type] = en
    save_data(data)
    if lock_type == "group":
        bot.send_message(m.chat.id, "🔒 گروه به دستور مدیر بسته شد." if en else "🔓 گروه توسط مدیر باز شد.")
    else:
        bot.reply_to(m, f"🔒 قفل {key_fa} فعال شد" if en else f"🔓 قفل {key_fa} غیرفعال شد")

# ================= 👑 مدیران و سودو =================
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "افزودن مدیر")
def add_admin(m):
    if not is_sudo(m.from_user.id): return
    data = load_data(); gid = str(m.chat.id)
    uid = str(m.reply_to_message.from_user.id)
    data["admins"].setdefault(gid, [])
    if uid not in data["admins"][gid]:
        data["admins"][gid].append(uid); save_data(data)
        bot.reply_to(m, f"✅ مدیر {uid} افزوده شد.")
    else:
        bot.reply_to(m, "⚠️ این کاربر از قبل مدیر است.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "افزودن سودو")
def add_sudo(m):
    if m.from_user.id != SUDO_ID: return
    data = load_data(); uid = str(m.reply_to_message.from_user.id)
    if uid in data["sudo_list"]: return bot.reply_to(m, "⚠️ از قبل سودو است.")
    data["sudo_list"].append(uid); save_data(data)
    bot.reply_to(m, f"👑 کاربر {uid} سودو شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست مدیران")
def list_admins(m):
    data = load_data(); gid = str(m.chat.id)
    lst = data["admins"].get(gid, [])
    if not lst: return bot.reply_to(m, "❗ مدیری وجود ندارد.")
    txt = "\n".join(lst)
    bot.reply_to(m, "👑 مدیران:\n" + txt)

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست سودوها")
def list_sudo(m):
    data = load_data(); lst = data["sudo_list"]
    if not lst: return bot.reply_to(m, "❗ هیچ سودوی اضافه‌شده‌ای نیست.")
    txt = "\n".join(lst)
    bot.reply_to(m, "👑 سودوها:\n" + txt)

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
        bot.reply_to(m, "❗ خطا در بن.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف بن")
def unban(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    bot.unban_chat_member(m.chat.id, uid, only_if_banned=True)
    bot.reply_to(m, f"✅ بن {uid} حذف شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "سکوت")
def mute_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    perms = types.ChatPermissions(can_send_messages=False)
    bot.restrict_chat_member(m.chat.id, m.reply_to_message.from_user.id, permissions=perms)
    bot.reply_to(m, "🔇 کاربر در سکوت قرار گرفت.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف سکوت")
def unmute_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    perms = types.ChatPermissions(can_send_messages=True)
    bot.restrict_chat_member(m.chat.id, m.reply_to_message.from_user.id, permissions=perms)
    bot.reply_to(m, "🔊 سکوت حذف شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "اخطار")
def warn_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    data = load_data(); gid = str(m.chat.id); uid = str(m.reply_to_message.from_user.id)
    data["warns"].setdefault(gid, {})
    data["warns"][gid][uid] = data["warns"][gid].get(uid, 0) + 1
    count = data["warns"][gid][uid]
    save_data(data)
    if count >= 3:
        bot.ban_chat_member(m.chat.id, int(uid))
        data["warns"][gid][uid] = 0; save_data(data)
        bot.reply_to(m, f"🚫 کاربر {uid} به دلیل ۳ اخطار بن شد.")
    else:
        bot.reply_to(m, f"⚠️ اخطار {count}/3 برای کاربر {uid} ثبت شد.")

# ================= 😂 جوک / 🔮 فال =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ثبت جوک" and m.reply_to_message)
def add_joke(m):
    d = load_data(); d["jokes"].append(m.reply_to_message.text); save_data(d)
    bot.reply_to(m, "😂 جوک ثبت شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "جوک")
def joke(m):
    d = load_data(); jokes = d["jokes"]
    if not jokes: return bot.reply_to(m, "❗ جوکی ثبت نشده.")
    bot.reply_to(m, random.choice(jokes))

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "لیست جوک‌ها")
def list_jokes(m):
    d = load_data(); jokes = d["jokes"]
    if not jokes: return bot.reply_to(m, "❗ جوکی ثبت نشده.")
    bot.reply_to(m, "\n".join([f"{i+1}. {t}" for i,t in enumerate(jokes)]))

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).startswith("حذف جوک "))
def del_joke(m):
    d = load_data(); jokes = d["jokes"]
    try:
        idx = int(cmd_text(m).split()[2]) - 1
        jokes.pop(idx); save_data(d)
        bot.reply_to(m, "🗑 جوک حذف شد.")
    except:
        bot.reply_to(m, "❗ شماره نامعتبر است.")

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ثبت فال" and m.reply_to_message)
def add_fal(m):
    d = load_data(); d["falls"].append(m.reply_to_message.text); save_data(d)
    bot.reply_to(m, "🔮 فال ثبت شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "فال")
def fal(m):
    d = load_data(); falls = d["falls"]
    if not falls: return bot.reply_to(m, "❗ فالی ثبت نشده.")
    bot.reply_to(m, random.choice(falls))

# ================= 📢 ارسال همگانی =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ارسال" and m.reply_to_message)
def broadcast(m):
    d = load_data(); users = list(set(d["users"])); groups = list(d["welcome"].keys())
    msg = m.reply_to_message; total = 0
    for uid in users + groups:
        try:
            if msg.text: bot.send_message(uid, msg.text)
            elif msg.photo: bot.send_photo(uid, msg.photo[-1].file_id, caption=msg.caption or "")
            total += 1
        except: continue
    bot.reply_to(m, f"📢 ارسال به {total} کاربر انجام شد.")

# ================= 🧹 پاکسازی =================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "پاکسازی")
def clear(m):
    c = 0
    for i in range(1, 101):
        try:
            bot.delete_message(m.chat.id, m.message_id - i); c += 1
        except: pass
    bot.reply_to(m, f"🧹 {c} پیام پاک شد.")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("حذف "))
def del_num(m):
    try:
        n = int(cmd_text(m).split()[1])
    except:
        return bot.reply_to(m, "❗ فرمت درست: حذف 10")
    c = 0
    for i in range(1, n + 1):
        try:
            bot.delete_message(m.chat.id, m.message_id - i); c += 1
        except: pass
    bot.reply_to(m, f"🗑 {c} پیام حذف شد.")

# ================= 👑 پاسخ ربات به سودو =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).lower() in ["سلام", "ربات"])
def sudo_greet(m):
    bot.reply_to(m, f"👑 سلام {m.from_user.first_name}!\nربات در خدمت سودوی عزیز است ✨")

# ================= 📊 آمار روزانه =================
@bot.message_handler(func=lambda m: cmd_text(m) == "آمار")
def group_stats(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)):
        return
    d = load_data()
    gid = str(m.chat.id)
    register_group(gid)
    st = d["stats"][gid]
    today = shamsi_date()
    hour = shamsi_time()

    # ریست روزانه آمار
    today_str = str(datetime.now().date())
    if st["date"] != today_str:
        st["date"] = today_str
        st["users"] = {}
        for k in st["counts"]:
            st["counts"][k] = 0
        save_data(d)

    total = sum(st["counts"].values())
    top_user = "هیچ فعالیتی ثبت نشده است!"
    if st["users"]:
        top_id = max(st["users"], key=st["users"].get)
        count = st["users"][top_id]
        try:
            name = bot.get_chat_member(m.chat.id, int(top_id)).user.first_name
        except:
            name = str(top_id)
        top_user = f"• نفر اول🥇 : ({count} پیام | {name})"

    msg = f"""♡ فعالیت‌های امروز تا این لحظه :
➲ تاریخ : {today}
➲ ساعت : {hour}
✛ کل پیام‌ها : {total}
✛ پیام فورواردی : {st['counts']['fwd']}
✛ فیلم : {st['counts']['video']}
✛ آهنگ : {st['counts']['music']}
✛ ویس : {st['counts']['voice']}
✛ عکس : {st['counts']['photo']}
✛ گیف : {st['counts']['gif']}
✛ استیکر : {st['counts']['sticker']}

✶ فعال‌ترین عضو گروه :
{top_user}

✶ کاربران برتر در افزودن عضو :
هیچ فعالیتی ثبت نشده است!

✧ اعضای وارد شده با لینک : ۰
✧ اعضای اد شده : ۰
✧ کل اعضای وارد شده : ۰
✧ اعضای اخراج‌شده : ۰
✧ اعضای سکوت‌شده : ۰
✧ اعضای لفت داده : ۰"""
    bot.reply_to(m, msg)

# ================= ثبت کاربران =================
@bot.message_handler(commands=['start'])
def start(m):
    d = load_data()
    uid = str(m.from_user.id)
    if uid not in d["users"]:
        d["users"].append(uid)
        save_data(d)
    bot.reply_to(m, f"سلام {m.from_user.first_name} 👋\nبه ربات مدیریتی خوش اومدی 🌟")

# ================= 🚀 اجرای ربات =================
print("🤖 Bot is running without errors...")
bot.infinity_polling(timeout=60, long_polling_timeout=30)
