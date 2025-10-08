# -*- coding: utf-8 -*-
import os, json, random, re
from datetime import datetime
import pytz, jdatetime
import telebot

# ================== ⚙️ تنظیمات ==================
TOKEN   = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
sudo_ids = {SUDO_ID}

# ================== 💾 فایل داده ==================
DATA_FILE = "data.json"
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"groups": {}, "welcome": {}, "autolock": {}, "locks": {}}, f, ensure_ascii=False, indent=2)

def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"groups": {}, "welcome": {}, "autolock": {}, "locks": {}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fix_data():
    data = load_data()
    for key in ["welcome", "groups", "autolock", "locks"]:
        if key not in data:
            data[key] = {}
    save_data(data)
    return data

# ================== 🧩 توابع کمکی ==================
def is_sudo(uid): return uid in sudo_ids
def is_admin(chat_id, user_id):
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator", "creator")
    except: return False

def cmd_text(m): return (getattr(m, "text", None) or "").strip()

# ================== 🕓 عمومی ==================
@bot.message_handler(func=lambda m: cmd_text(m) == "ساعت")
def cmd_time(m):
    now_utc = datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
    now_teh = datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
    bot.reply_to(m, f"⏰ UTC: {now_utc}\n⏰ تهران: {now_teh}")

@bot.message_handler(func=lambda m: cmd_text(m) == "آمار")
def cmd_stats(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    try: count = bot.get_chat_member_count(m.chat.id)
    except: count = "نامشخص"
    bot.reply_to(m, f"📊 اعضای گروه: {count}")

@bot.message_handler(func=lambda m: cmd_text(m) == "ایدی")
def cmd_id(m):
    caption = f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 گروه: <code>{m.chat.id}</code>"
    bot.reply_to(m, caption)

SUDO_RESPONSES = ["جونم قربان 😎", "در خدمتم ✌️", "ربات آماده‌ست 🚀", "چه خبر رئیس؟ 🤖"]
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ربات")
def cmd_sudo(m): bot.reply_to(m, random.choice(SUDO_RESPONSES))

# ================== 🎉 خوشامد ==================
def now_time():
    return jdatetime.datetime.now().strftime("%H:%M  ( %A %d %B %Y )")

@bot.message_handler(content_types=["new_chat_members"])
def welcome_new_member(m):
    try:
        data = fix_data()
        group = str(m.chat.id)
        settings = data["welcome"].get(group, {"enabled": True, "type": "text", "content": None})
        if not settings.get("enabled", True): return
        name = m.new_chat_members[0].first_name or "دوست جدید"
        time_str = now_time()
        text = settings.get("content") or (
            f"سلام {name} عزیز 🌙\n"
            f"به گروه StarryNight خوش اومدی 😎\n\n"
            f"⏰ ساعت الان: {time_str}"
        )
        bot.send_message(m.chat.id, text)
    except Exception as e:
        print(f"⚠️ welcome error: {e}")

@bot.message_handler(func=lambda m: cmd_text(m) in ["خوشامد روشن", "خوشامد خاموش"])
def toggle_welcome(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    data = fix_data()
    group = str(m.chat.id)
    en = (cmd_text(m) == "خوشامد روشن")
    data["welcome"].setdefault(group, {"enabled": True})
    data["welcome"][group]["enabled"] = en
    save_data(data)
    bot.reply_to(m, "✅ خوشامد روشن شد" if en else "🚫 خوشامد خاموش شد")

@bot.message_handler(func=lambda m: cmd_text(m) == "تنظیم خوشامد متن" and m.reply_to_message)
def set_welcome_text(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    data = fix_data()
    group = str(m.chat.id)
    txt = m.reply_to_message.text or ""
    data["welcome"][group] = {"enabled": True, "type": "text", "content": txt}
    save_data(data)
    bot.reply_to(m, "📝 متن خوشامد تنظیم شد.")

# ================== 🔒 قفل‌ها ==================
@bot.message_handler(func=lambda m: cmd_text(m).startswith("قفل "))
def lock_feature(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    feature = cmd_text(m).replace("قفل ", "").strip()
    data = fix_data()
    data["locks"].setdefault(str(m.chat.id), {})[feature] = True
    save_data(data)
    bot.reply_to(m, f"🔒 قفل {feature} فعال شد")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("باز کردن "))
def unlock_feature(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    feature = cmd_text(m).replace("باز کردن ", "").strip()
    data = fix_data()
    data["locks"].setdefault(str(m.chat.id), {})[feature] = False
    save_data(data)
    bot.reply_to(m, f"🔓 قفل {feature} غیرفعال شد")

# کنترل پیام‌ها
@bot.message_handler(content_types=["text", "photo", "video", "document", "sticker"])
def check_locks(m):
    data = fix_data()
    locks = data["locks"].get(str(m.chat.id), {})
    if locks.get("گروه") and not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)):
        bot.delete_message(m.chat.id, m.message_id)
        return
    if locks.get("لینک") and re.search(r"(https?://|t\.me|telegram\.me)", m.text or ""):
        bot.delete_message(m.chat.id, m.message_id)

# ================== 🚫 بن / سکوت / اخطار ==================
banned = {}; muted = {}; warns = {}; MAX_WARN = 3

def protect(chat_id, uid):
    if is_sudo(uid): return "⚡ این کاربر سودو است"
    try:
        st = bot.get_chat_member(chat_id, uid).status
        if st == "creator": return "❗ صاحب گروه قابل مدیریت نیست"
    except: pass
    return None

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "بن")
def cmd_ban(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    p = protect(m.chat.id, uid)
    if p: return bot.reply_to(m, p)
    bot.ban_chat_member(m.chat.id, uid)
    banned.setdefault(m.chat.id, set()).add(uid)
    bot.reply_to(m, "🚫 کاربر بن شد")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف بن")
def cmd_unban(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    bot.unban_chat_member(m.chat.id, uid)
    banned.get(m.chat.id, set()).discard(uid)
    bot.reply_to(m, "✅ بن حذف شد")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست بن")
def list_ban(m):
    ids = banned.get(m.chat.id, set())
    if not ids: return bot.reply_to(m, "❗ لیست بن خالی است")
    bot.reply_to(m, "\n".join([f"▪️ {i}" for i in ids]))

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "سکوت")
def cmd_mute(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    p = protect(m.chat.id, uid)
    if p: return bot.reply_to(m, p)
    bot.restrict_chat_member(m.chat.id, uid, can_send_messages=False)
    muted.setdefault(m.chat.id, set()).add(uid)
    bot.reply_to(m, "🔇 کاربر در سکوت قرار گرفت")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف سکوت")
def cmd_unmute(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    bot.restrict_chat_member(m.chat.id, uid, can_send_messages=True)
    muted.get(m.chat.id, set()).discard(uid)
    bot.reply_to(m, "🔊 سکوت حذف شد")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست سکوت")
def list_mute(m):
    ids = muted.get(m.chat.id, set())
    if not ids: return bot.reply_to(m, "❗ لیست سکوت خالی است")
    bot.reply_to(m, "\n".join([f"▪️ {i}" for i in ids]))

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "اخطار")
def cmd_warn(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    warns.setdefault(m.chat.id, {})
    warns[m.chat.id][uid] = warns[m.chat.id].get(uid, 0) + 1
    c = warns[m.chat.id][uid]
    if c >= MAX_WARN:
        bot.ban_chat_member(m.chat.id, uid)
        warns[m.chat.id][uid] = 0
        bot.reply_to(m, "🚫 کاربر با ۳ اخطار بن شد")
    else:
        bot.reply_to(m, f"⚠️ اخطار {c}/{MAX_WARN}")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف اخطار")
def cmd_clearwarn(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    warns.get(m.chat.id, {}).pop(uid, None)
    bot.reply_to(m, "✅ اخطارها حذف شد")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست اخطار")
def list_warn(m):
    w = warns.get(m.chat.id, {})
    if not w: return bot.reply_to(m, "❗ لیست اخطار خالی است")
    txt = "\n".join([f"▪️ {u} — {c} اخطار" for u, c in w.items()])
    bot.reply_to(m, txt)

# ================== 🧹 پاکسازی ==================
@bot.message_handler(func=lambda m: (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)) and cmd_text(m)=="پاکسازی")
def clear_all(m):
    deleted=0
    try:
        for i in range(1,201):
            bot.delete_message(m.chat.id,m.message_id-i)
            deleted+=1
    except: pass
    bot.reply_to(m,f"🧹 {deleted} پیام پاک شد")

# ================== 🚀 اجرای نهایی ==================
if __name__ == "__main__":
    print("🤖 Bot is running...")
    try:
        bot.infinity_polling(skip_pending=True, timeout=30)
    except Exception as e:
        print(f"❌ Polling error: {e}")
