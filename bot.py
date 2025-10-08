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

# ================= 🔒 قفل‌ها =================
LOCK_MAP = {
    "لینک": "link", "گروه": "group", "عکس": "photo", "ویدیو": "video",
    "استیکر": "sticker", "گیف": "gif", "فایل": "file",
    "موزیک": "music", "ویس": "voice", "فوروارد": "forward"
}

# ================= 📂 داده‌ها =================
def _base_data():
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

def _ensure_datafile():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(_base_data(), f, ensure_ascii=False, indent=2)

def load_data():
    _ensure_datafile()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = _base_data()
        save_data(data)
    base = _base_data()
    for k in base:
        if k not in data:
            data[k] = base[k]
    save_data(data)
    return data

def save_data(d):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"save_data: {e}")

# ================= 🕒 زمان و تاریخ =================
def now_teh_dt():
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

# ================= 🛠 ابزارها =================
def cmd_text(m): return (getattr(m, "text", None) or "").strip()

def is_sudo(uid):
    d = load_data()
    return str(uid) in [str(SUDO_ID)] + [str(x) for x in d.get("sudo_list", [])]

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

# ================= 👋 استارت =================
@bot.message_handler(commands=["start"])
def start_cmd(m):
    d = load_data()
    u = str(m.from_user.id)
    if "users" not in d: d["users"] = []
    if u not in [str(x) for x in d["users"]]:
        d["users"].append(int(u))
        save_data(d)
    bot.reply_to(m, "سلام 👋\nمن ربات مدیریتی شما هستم.\nبرای پنل بنویس: «پنل» یا /panel")

# ================= 📜 آیدی / ساعت / لینک =================
@bot.message_handler(func=lambda m: cmd_text(m) in ["آیدی","ایدی"])
def show_id(m):
    try:
        caption = (f"🧾 <b>نام:</b> {m.from_user.first_name}\n"
                   f"🆔 <b>آیدی شما:</b> <code>{m.from_user.id}</code>\n"
                   f"💬 <b>آیدی گروه:</b> <code>{m.chat.id}</code>\n"
                   f"📅 {shamsi_date()} | ⏰ {shamsi_time()}")
        ph = bot.get_user_profile_photos(m.from_user.id, limit=1)
        if ph.total_count > 0:
            bot.send_photo(m.chat.id, ph.photos[0][-1].file_id, caption=caption)
        else:
            bot.reply_to(m, caption)
    except Exception as e:
        logging.error(f"show_id: {e}")
        bot.reply_to(m, f"🆔 <code>{m.from_user.id}</code> | ⏰ {shamsi_time()}")

@bot.message_handler(func=lambda m: cmd_text(m) == "ساعت")
def show_time(m):
    bot.reply_to(m, f"⏰ {shamsi_time()}\n📅 {shamsi_date()}")

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
        bot.reply_to(m, "⚠️ دسترسی ساخت/دریافت لینک ندارم.")

# ================= 👋 خوشامد =================
@bot.message_handler(content_types=["new_chat_members"])
def welcome(m):
    register_group(m.chat.id)
    d = load_data(); gid = str(m.chat.id)
    s = d["welcome"].get(gid, {"enabled": True})
    if not s.get("enabled", True): return
    user = m.new_chat_members[0]
    name = user.first_name or "دوست جدید"
    text = s.get("content") or f"سلام {name} 🌹\nبه {m.chat.title} خوش اومدی 🌸\n⏰ {shamsi_time()}"
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
    bot.reply_to(m, "✅ پیام خوشامد جدید تنظیم شد. از {name} و {time} هم می‌تونی استفاده کنی.")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) in ["خوشامد روشن", "خوشامد خاموش"])
def toggle_welcome(m):
    data = load_data(); gid = str(m.chat.id)
    en = cmd_text(m) == "خوشامد روشن"
    data["welcome"].setdefault(gid, {"enabled": True})
    data["welcome"][gid]["enabled"] = en
    save_data(data)
    bot.reply_to(m, "🟢 خوشامد روشن شد" if en else "🔴 خوشامد خاموش شد")# ================= 🔒 قفل‌ها: فعال/غیرفعال =================
@bot.message_handler(func=lambda m: cmd_text(m).startswith("قفل ") or cmd_text(m).startswith("بازکردن "))
def toggle_lock(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    d = load_data(); gid = str(m.chat.id)
    part = cmd_text(m).split()
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
    msg = f"{'🔒' if en else '🔓'} قفل {key_fa} {'فعال' if en else 'غیرفعال'} شد."
    bot.reply_to(m, msg)

# ================= 🚧 اعمال قفل‌ها + آمار =================
@bot.message_handler(content_types=['text','photo','video','document','audio','voice','sticker','animation','video_note'])
def enforce_and_stats(m):
    try:
        register_group(m.chat.id)
        d = load_data(); gid = str(m.chat.id)
        if not is_admin(m.chat.id, m.from_user.id):
            locks = d["locks"].get(gid, {})
            txt = (m.text or "") + " " + (getattr(m, "caption", "") or "")
            if locks.get("group"): bot.delete_message(m.chat.id, m.message_id); return
            if locks.get("link") and any(x in txt for x in ["http://","https://","t.me","telegram.me"]):
                bot.delete_message(m.chat.id, m.message_id)
                bot.send_message(m.chat.id, "🚫 ارسال لینک مجاز نیست.", disable_notification=True); return
            if locks.get("photo") and m.photo:
                bot.delete_message(m.chat.id, m.message_id)
                bot.send_message(m.chat.id, "🖼 ارسال عکس ممنوع است.", disable_notification=True); return
            if locks.get("video") and m.video:
                bot.delete_message(m.chat.id, m.message_id)
                bot.send_message(m.chat.id, "🎬 ارسال ویدیو مجاز نیست.", disable_notification=True); return
            if locks.get("sticker") and m.sticker:
                bot.delete_message(m.chat.id, m.message_id)
                bot.send_message(m.chat.id, "😜 ارسال استیکر ممنوع است.", disable_notification=True); return
            if locks.get("gif") and m.animation:
                bot.delete_message(m.chat.id, m.message_id)
                bot.send_message(m.chat.id, "🎞 ارسال گیف مجاز نیست.", disable_notification=True); return
            if locks.get("file") and m.document:
                bot.delete_message(m.chat.id, m.message_id)
                bot.send_message(m.chat.id, "📎 ارسال فایل بسته است.", disable_notification=True); return
            if locks.get("music") and m.audio:
                bot.delete_message(m.chat.id, m.message_id)
                bot.send_message(m.chat.id, "🎵 ارسال موزیک مجاز نیست.", disable_notification=True); return
            if locks.get("voice") and m.voice:
                bot.delete_message(m.chat.id, m.message_id)
                bot.send_message(m.chat.id, "🎙 ارسال ویس بسته است.", disable_notification=True); return
            if locks.get("forward") and (m.forward_from or m.forward_from_chat):
                bot.delete_message(m.chat.id, m.message_id)
                bot.send_message(m.chat.id, "⚠️ فوروارد در این گروه ممنوع است.", disable_notification=True); return

        # ثبت آمار
        today = str(datetime.now().date())
        st = d["stats"].setdefault(gid, {"date": today, "users": {}, "counts": {k:0 for k in ["msg","photo","video","voice","music","sticker","gif","fwd"]}})
        if st["date"] != today:
            st["date"] = today; st["users"] = {}; st["counts"] = {k:0 for k in st["counts"]}
        uid = str(m.from_user.id)
        st["users"][uid] = st["users"].get(uid, 0) + 1
        if m.photo: st["counts"]["photo"] += 1
        elif m.video: st["counts"]["video"] += 1
        elif m.voice: st["counts"]["voice"] += 1
        elif m.audio: st["counts"]["music"] += 1
        elif m.sticker: st["counts"]["sticker"] += 1
        elif m.animation: st["counts"]["gif"] += 1
        elif (m.forward_from or m.forward_from_chat): st["counts"]["fwd"] += 1
        else: st["counts"]["msg"] += 1
        save_data(d)
    except Exception as e:
        logging.error(f"enforce_and_stats: {e}")

# ================= 💬 آمار =================
@bot.message_handler(func=lambda m: cmd_text(m) == "آمار")
def group_stats(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    d = load_data(); gid = str(m.chat.id)
    register_group(gid)
    st = d["stats"].get(gid, {})
    counts = st.get("counts", {k: 0 for k in ["msg","photo","video","voice","music","sticker","gif","fwd"]})
    total = sum(counts.values())
    if st.get("users"):
        top_uid = max(st["users"], key=st["users"].get)
        try: top_name = bot.get_chat_member(m.chat.id, int(top_uid)).user.first_name
        except: top_name = top_uid
        top_line = f"• فعال‌ترین عضو: {top_name} ({st['users'][top_uid]} پیام)"
    else:
        top_line = "هیچ فعالیتی ثبت نشده است!"
    msg = f"""📊 آمار امروز:
📅 {shamsi_date()} | ⏰ {shamsi_time()}
💬 کل پیام‌ها: {total}
🖼 عکس: {counts['photo']} | 🎬 ویدیو: {counts['video']}
🎵 موزیک: {counts['music']} | 🎙 ویس: {counts['voice']}
😜 استیکر: {counts['sticker']} | 🎞 گیف: {counts['gif']}
⚠️ فوروارد: {counts['fwd']}
{top_line}"""
    bot.reply_to(m, msg)

# ================= 😂 جوک و 🔮 فال =================
@bot.message_handler(func=lambda m: cmd_text(m) == "جوک")
def joke(m):
    d = load_data(); j = d.get("jokes", [])
    bot.reply_to(m, random.choice(j) if j else "😅 هنوز جوکی ثبت نشده.")

@bot.message_handler(func=lambda m: cmd_text(m) == "فال")
def fal(m):
    d = load_data(); f = d.get("falls", [])
    bot.reply_to(m, random.choice(f) if f else "🔮 هنوز فالی ثبت نشده.")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "ثبت جوک")
def add_joke(m):
    d = load_data(); txt = (m.reply_to_message.text or "").strip()
    if not txt: return bot.reply_to(m, "⚠️ فقط متن رو ریپلای کن.")
    d["jokes"].append(txt); save_data(d)
    bot.reply_to(m, "😂 جوک ذخیره شد.")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "ثبت فال")
def add_fal(m):
    d = load_data(); txt = (m.reply_to_message.text or "").strip()
    if not txt: return bot.reply_to(m, "⚠️ فقط متن رو ریپلای کن.")
    d["falls"].append(txt); save_data(d)
    bot.reply_to(m, "🔮 فال ذخیره شد.")

# ================= 🧹 پاکسازی =================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("حذف "))
def delete_n(m):
    try: n = int(cmd_text(m).split()[1])
    except: return bot.reply_to(m, "❗ فرمت درست: حذف 20")
    deleted = 0
    for i in range(1, n+1):
        try: bot.delete_message(m.chat.id, m.message_id - i); deleted += 1
        except: pass
    bot.send_message(m.chat.id, f"🧹 {deleted} پیام پاک شد.", disable_notification=True)

# ================= 🎛️ پنل شیشه‌ای =================
def main_panel():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🔒 قفل‌ها", callback_data="locks"),
        types.InlineKeyboardButton("👋 خوشامد", callback_data="welcome"),
        types.InlineKeyboardButton("😂 جوک و فال", callback_data="fun"),
        types.InlineKeyboardButton("📊 آمار", callback_data="stats"),
        types.InlineKeyboardButton("ℹ️ راهنما", callback_data="help"),
        types.InlineKeyboardButton("🔙 بستن", callback_data="close")
    )
    return kb

@bot.message_handler(commands=["panel", "پنل"])
def open_panel(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    bot.send_message(m.chat.id, "🎛️ <b>پنل مدیریتی فعال شد!</b>\nاز دکمه‌ها استفاده کن 👇", reply_markup=main_panel())

@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    data = call.data
    if data == "close":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
    elif data == "help":
        txt = ("📘 <b>دستورات سریع:</b>\n"
               "• آیدی / ساعت / آمار\n"
               "• قفل/بازکردن عکس، فیلم، استیکر، لینک...\n"
               "• خوشامد روشن/خاموش + تنظیم خوشامد\n"
               "• ثبت جوک / فال / حذف N پیام\n"
               "• پنل سودو برای تنظیمات بیشتر")
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="main"))
        try: bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, reply_markup=kb)
        except: pass
    elif data == "main":
        try: bot.edit_message_text("🎛️ منوی اصلی:", call.message.chat.id, call.message.message_id, reply_markup=main_panel())
        except: pass

# ================= 👑 پاسخ مخصوص سودو =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).lower() in ["سلام","ربات","bot"])
def sudo_reply(m):
    bot.reply_to(m, f"سلام 👑 {m.from_user.first_name}!\nدر خدمتتم سودوی عزیز 🤖")

# ================= 🚀 اجرای ربات =================
if __name__ == "__main__":
    print("🤖 ربات مدیریتی Persian Lux Panel – آماده به کار!")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            logging.error(f"polling crash: {e}")
            time.sleep(5)
