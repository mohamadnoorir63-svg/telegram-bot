# -*- coding: utf-8 -*-
import os, json, random, logging
from datetime import datetime
import pytz, jdatetime
import telebot
from telebot import types

# ================= ⚙️ تنظیمات اولیه =================
TOKEN = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

DATA_FILE = "data.json"
LOG_FILE = "error.log"

logging.basicConfig(filename=LOG_FILE, level=logging.ERROR,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# ================= 🔒 قفل‌ها =================
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
    for k in base_data():
        if k not in data:
            data[k] = base_data()[k]
    save_data(data)
    return data

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

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

# ================= ⚙️ ابزارها =================
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

# ================= 🎛️ پنل شیشه‌ای چندصفحه‌ای =================
def main_panel():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🔒 قفل‌ها", callback_data="locks"),
        types.InlineKeyboardButton("👋 خوشامد", callback_data="welcome"),
        types.InlineKeyboardButton("🚫 بن / اخطار", callback_data="ban"),
        types.InlineKeyboardButton("😂 جوک و فال", callback_data="fun"),
        types.InlineKeyboardButton("📊 آمار", callback_data="stats"),
        types.InlineKeyboardButton("🧹 پاکسازی", callback_data="clear"),
        types.InlineKeyboardButton("📢 ارسال", callback_data="broadcast"),
        types.InlineKeyboardButton("👥 مدیران", callback_data="admins"),
        types.InlineKeyboardButton("👑 سودوها", callback_data="sudos"),
        types.InlineKeyboardButton("ℹ️ راهنما", callback_data="help")
    )
    return kb

@bot.message_handler(commands=["panel", "پنل"])
def open_panel(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)):
        return
    bot.send_message(
        m.chat.id,
        "🎛️ <b>پنل مدیریتی حرفه‌ای فعال شد!</b>\nاز دکمه‌های زیر برای کنترل ربات استفاده کنید 👇",
        reply_markup=main_panel()
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    data = call.data
    if data == "help":
        txt = (
            "📘 <b>راهنمای سریع ربات:</b>\n\n"
            "• قفل لینک، گیف، عکس و ...\n"
            "• تنظیم خوشامد متنی یا تصویری\n"
            "• نمایش آمار روزانه، ساعت و آیدی\n"
            "• ثبت و نمایش جوک و فال\n"
            "• افزودن مدیر و سودو\n"
            "• ارسال همگانی و پاکسازی گروه\n"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back"))
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, reply_markup=kb)
    elif data == "back":
        bot.edit_message_text("🎛️ بازگشت به منوی اصلی:", call.message.chat.id, call.message.message_id, reply_markup=main_panel())

# ================= 💬 آمار روزانه =================
@bot.message_handler(func=lambda m: cmd_text(m) == "آمار")
def group_stats(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    d = load_data(); gid = str(m.chat.id)
    register_group(gid)
    st = d["stats"][gid]
    today = shamsi_date(); hour = shamsi_time()
    total = sum(st["counts"].values())
    if st["users"]:
        top_user_id = max(st["users"], key=st["users"].get)
        try:
            user = bot.get_chat_member(m.chat.id, int(top_user_id)).user.first_name
        except:
            user = f"{top_user_id}"
        top_user = f"• نفر اول🥇 : ({st['users'][top_user_id]} پیام | {user})"
    else:
        top_user = "هیچ فعالیتی ثبت نشده است!"
    msg = f"""♡ فعالیت‌های امروز تا این لحظه:
➲ تاریخ: {today}
➲ ساعت: {hour}
✛ کل پیام‌ها: {total}
✛ فوروارد: {st['counts']['fwd']}
✛ فیلم: {st['counts']['video']}
✛ آهنگ: {st['counts']['music']}
✛ ویس: {st['counts']['voice']}
✛ عکس: {st['counts']['photo']}
✛ گیف: {st['counts']['gif']}
✛ استیکر: {st['counts']['sticker']}
✶ فعال‌ترین عضو:
{top_user}
📆 آخرین بروزرسانی: {now_teh().strftime('%Y-%m-%d %H:%M:%S')}
"""
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

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "تنظیم خوشامد" and m.reply_to_message)
def set_welcome(m):
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

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) in ["خوشامد روشن", "خوشامد خاموش"])
def toggle_welcome(m):
    data = load_data(); gid = str(m.chat.id)
    en = cmd_text(m) == "خوشامد روشن"
    data["welcome"].setdefault(gid, {"enabled": True})
    data["welcome"][gid]["enabled"] = en
    save_data(data)
    bot.reply_to(m, "✅ خوشامد روشن شد" if en else "🚫 خوشامد خاموش شد")

# ================= 🔗 لینک‌ها =================
@bot.message_handler(func=lambda m: cmd_text(m) == "لینک گروه")
def group_link(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        link = bot.export_chat_invite_link(m.chat.id)
        bot.reply_to(m, f"🔗 لینک گروه:\n{link}")
    except:
        bot.reply_to(m, "❌ خطا در دریافت لینک گروه.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لینک ربات")
def bot_link(m):
    bot.reply_to(m, f"🤖 لینک ربات:\nhttps://t.me/{bot.get_me().username}")

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

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("حذف جوک "))
def del_joke(m):
    data = load_data(); jokes = data.get("jokes", [])
    try:
        num = int(cmd_text(m).split(" ")[2]) - 1
        jokes.pop(num)
        data["jokes"] = jokes
        save_data(data)
        bot.reply_to(m, "🗑 جوک حذف شد.")
    except:
        bot.reply_to(m, "❌ شماره جوک نامعتبر است.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست جوک‌ها")
def list_jokes(m):
    data = load_data(); jokes = data.get("jokes", [])
    if not jokes: return bot.reply_to(m, "❗ جوکی ثبت نشده.")
    text = "\n".join([f"{i+1}. {j}" for i, j in enumerate(jokes)])
    bot.reply_to(m, "📜 لیست جوک‌ها:\n" + text)

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

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست فال‌ها")
def list_fals(m):
    data = load_data(); falls = data.get("falls", [])
    if not falls: return bot.reply_to(m, "❗ فالی ثبت نشده.")
    text = "\n".join([f"{i+1}. {f}" for i, f in enumerate(falls)])
    bot.reply_to(m, "📜 لیست فال‌ها:\n" + text)

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("حذف فال "))
def del_fal(m):
    data = load_data(); falls = data.get("falls", [])
    try:
        num = int(cmd_text(m).split(" ")[2]) - 1
        falls.pop(num)
        data["falls"] = falls
        save_data(data)
        bot.reply_to(m, "🗑 فال حذف شد.")
    except:
        bot.reply_to(m, "❌ شماره فال نامعتبر است.")

# ================= 👑 مدیر و سودو =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "لیست سودوها")
def list_sudos(m):
    d = load_data()
    sudos = d.get("sudo_list", [])
    if not sudos:
        bot.reply_to(m, "❗ هیچ سودویی ثبت نشده.")
    else:
        txt = "\n".join([f"{i+1}. {u}" for i, u in enumerate(sudos)])
        bot.reply_to(m, "👑 لیست سودوها:\n" + txt)

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and m.reply_to_message and cmd_text(m) == "افزودن سودو")
def add_sudo(m):
    d = load_data()
    uid = str(m.reply_to_message.from_user.id)
    if uid not in d["sudo_list"]:
        d["sudo_list"].append(uid)
        save_data(d)
        bot.reply_to(m, f"👑 {uid} به سودوها اضافه شد.")
    else:
        bot.reply_to(m, "⚠️ این کاربر قبلاً سودو بود.")

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and m.reply_to_message and cmd_text(m) == "حذف سودو")
def remove_sudo(m):
    d = load_data()
    uid = str(m.reply_to_message.from_user.id)
    if uid in d["sudo_list"]:
        d["sudo_list"].remove(uid)
        save_data(d)
        bot.reply_to(m, "🗑 سودو حذف شد.")
    else:
        bot.reply_to(m, "❗ کاربر سودو نیست.")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "لیست مدیران")
def list_admins(m):
    d = load_data(); gid = str(m.chat.id)
    admins = d["admins"].get(gid, [])
    if not admins:
        bot.reply_to(m, "❗ هیچ مدیری ثبت نشده.")
    else:
        txt = "\n".join([f"{i+1}. {u}" for i, u in enumerate(admins)])
        bot.reply_to(m, "👥 لیست مدیران:\n" + txt)

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "افزودن مدیر")
def add_admin(m):
    d = load_data(); gid = str(m.chat.id)
    uid = str(m.reply_to_message.from_user.id)
    d["admins"].setdefault(gid, [])
    if uid not in d["admins"][gid]:
        d["admins"][gid].append(uid)
        save_data(d)
        bot.reply_to(m, f"👤 {uid} به مدیران اضافه شد.")
    else:
        bot.reply_to(m, "⚠️ این کاربر قبلاً مدیر بود.")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "حذف مدیر")
def remove_admin(m):
    d = load_data(); gid = str(m.chat.id)
    uid = str(m.reply_to_message.from_user.id)
    if uid in d["admins"].get(gid, []):
        d["admins"][gid].remove(uid)
        save_data(d)
        bot.reply_to(m, "🗑 مدیر حذف شد.")
    else:
        bot.reply_to(m, "❗ کاربر مدیر نیست.")

# ================= 🧹 پاکسازی =================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("پاکسازی "))
def clear_messages(m):
    try:
        num = int(cmd_text(m).split()[1])
        for i in range(num):
            bot.delete_message(m.chat.id, m.message_id - i)
        bot.send_message(m.chat.id, f"🧹 {num} پیام اخیر پاک شد.", disable_notification=True)
    except:
        bot.reply_to(m, "❗ عدد وارد شده نامعتبر است.")

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
    bot.reply_to(m, f"📢 پیام برای {total} کاربر ارسال شد.")

# ================= 👑 پاسخ سودو =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).lower() in ["سلام","ربات","bot"])
def sudo_reply(m):
    bot.reply_to(m, f"سلام 👑 {m.from_user.first_name}!\nدر خدمتتم سودوی عزیز 🤖")

# ================= 🚀 اجرای ربات =================
if __name__ == "__main__":
    print("🤖 ربات مدیریتی V13.6 Persian Pro با موفقیت فعال شد!")
    bot.infinity_polling(timeout=60, long_polling_timeout=30)
