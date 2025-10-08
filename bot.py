# -*- coding: utf-8 -*-
import os, json, random
from datetime import datetime
import pytz, jdatetime
import telebot
from telebot import types

# ================== ⚙️ تنظیمات ==================
TOKEN   = os.environ.get("BOT_TOKEN")  # باید ست شده باشد
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
sudo_ids = {SUDO_ID}

DATA_FILE = "data.json"

# ================== 📂 فایل دیتا ==================
def _base():
    return {
        "welcome": {},   # gid -> {enabled, type, content, file_id}
        "locks": {},     # gid -> {"link": bool, "group": bool}
        "banned": {},    # (برای گزارش ساده داخل رم)
        "muted":  {},    # (برای گزارش ساده داخل رم)
    }

def load_data():
    base = _base()
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(base, f, ensure_ascii=False, indent=2)
        return base
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        data = base
    # تضمین وجود کلیدها
    for k in base:
        if k not in data:
            data[k] = base[k]
    save_data(data)
    return data

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def register_group(gid):
    data = load_data()
    gid = str(gid)
    data["welcome"].setdefault(gid, {"enabled": True, "type": "text", "content": None})
    data["locks"].setdefault(gid, {"link": False, "group": False})
    save_data(data)

# ================== 🧩 کمکی ==================
def is_sudo(uid): return uid in sudo_ids
def is_admin(chat_id, uid):
    try:
        st = bot.get_chat_member(chat_id, uid).status
        return st in ("administrator", "creator")
    except:
        return False

def cmd_text(m): return (getattr(m, "text", None) or "").strip()

def now_tehran_str():
    return datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")

def now_time_shamsi():
    return jdatetime.datetime.now().strftime("%H:%M  (%A %d %B %Y)")

# ================== 💬 دستورات عمومی ==================
@bot.message_handler(func=lambda m: cmd_text(m)=="ساعت")
def cmd_time(m):
    now_utc = datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
    now_teh = now_tehran_str()
    bot.reply_to(m, f"⏰ UTC: {now_utc}\n⏰ تهران: {now_teh}")

@bot.message_handler(func=lambda m: cmd_text(m)=="آمار")
def cmd_stats(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    try: count = bot.get_chat_member_count(m.chat.id)
    except: count = "نامشخص"
    bot.reply_to(m, f"📊 اعضای گروه: {count}")

@bot.message_handler(func=lambda m: cmd_text(m) in ["آیدی","ایدی"])
def cmd_id(m):
    caption = f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 گروه: <code>{m.chat.id}</code>"
    try:
        photos = bot.get_user_profile_photos(m.from_user.id, limit=1)
        if photos.total_count > 0:
            bot.send_photo(m.chat.id, photos.photos[0][-1].file_id, caption=caption)
        else:
            bot.reply_to(m, caption)
    except:
        bot.reply_to(m, caption)

# ================== 🎉 خوشامد ==================
@bot.message_handler(content_types=["new_chat_members"])
def welcome(m):
    register_group(m.chat.id)
    data = load_data()
    gid = str(m.chat.id)
    s = data["welcome"].get(gid, {"enabled": True, "type": "text", "content": None})
    if not s.get("enabled", True): return

    name = m.new_chat_members[0].first_name or "دوست جدید"
    t = now_time_shamsi()
    text = s.get("content") or (f"سلام {name} 🌙\nبه گروه {m.chat.title} خوش اومدی 😎\n⏰ {t}")
    text = text.replace("{name}", name).replace("{time}", t)

    if s.get("type") == "photo" and s.get("file_id"):
        bot.send_photo(m.chat.id, s["file_id"], caption=text)
    else:
        bot.send_message(m.chat.id, text)

@bot.message_handler(func=lambda m: cmd_text(m) in ["خوشامد روشن", "خوشامد خاموش"])
def toggle_welcome(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    data = load_data(); gid = str(m.chat.id)
    data["welcome"].setdefault(gid, {"enabled": True})
    turn_on = (cmd_text(m) == "خوشامد روشن")
    data["welcome"][gid]["enabled"] = turn_on
    save_data(data)
    bot.reply_to(m, "✅ خوشامد روشن شد" if turn_on else "🚫 خوشامد خاموش شد")

@bot.message_handler(func=lambda m: cmd_text(m)=="تنظیم خوشامد" and m.reply_to_message)
def set_welcome(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    data = load_data(); gid = str(m.chat.id)
    txt = (m.reply_to_message.text or "").strip()
    data["welcome"][gid] = {"enabled": True, "type": "text", "content": txt}
    save_data(data)
    bot.reply_to(m, "📝 متن خوشامد تنظیم شد. از {name} و {time} می‌تونی استفاده کنی.")

# ================== 🔨 مدیریت کاربران ==================
banned = {}; muted = {}

def protect(chat_id, uid):
    if is_sudo(uid): return "⚡ این کاربر سودو است"
    try:
        st = bot.get_chat_member(chat_id, uid).status
        if st == "creator": return "❗ صاحب گروه قابل مدیریت نیست"
    except: pass
    return None

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="بن")
def ban_user(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    p = protect(m.chat.id, uid)
    if p: return bot.reply_to(m, p)
    try:
        bot.ban_chat_member(m.chat.id, uid)
        banned.setdefault(m.chat.id, set()).add(uid)
        bot.reply_to(m, f"🚫 کاربر {uid} بن شد")
    except Exception as e:
        bot.reply_to(m, f"❗ خطا در بن: {e}")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف بن")
def unban_user(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    try:
        bot.unban_chat_member(m.chat.id, uid, only_if_banned=True)
        banned.get(m.chat.id, set()).discard(uid)
        bot.reply_to(m, "✅ بن حذف شد")
    except Exception as e:
        bot.reply_to(m, f"❗ خطا در حذف بن: {e}")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="سکوت")
def mute_user(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    p = protect(m.chat.id, uid)
    if p: return bot.reply_to(m, p)
    try:
        perms = types.ChatPermissions(can_send_messages=False)
        bot.restrict_chat_member(m.chat.id, uid, permissions=perms)
        muted.setdefault(m.chat.id, set()).add(uid)
        bot.reply_to(m, f"🔇 کاربر {uid} در سکوت قرار گرفت")
    except Exception as e:
        bot.reply_to(m, f"❗ خطا در سکوت: {e}")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف سکوت")
def unmute_user(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    try:
        perms = types.ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
        bot.restrict_chat_member(m.chat.id, uid, permissions=perms)
        muted.get(m.chat.id, set()).discard(uid)
        bot.reply_to(m, "🔊 سکوت حذف شد")
    except Exception as e:
        bot.reply_to(m, f"❗ خطا در حذف سکوت: {e}")

# ================== 🧹 پاکسازی ==================
@bot.message_handler(func=lambda m:(is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)) and cmd_text(m)=="پاکسازی")
def clear(m):
    deleted = 0
    for i in range(1, 101):
        try:
            bot.delete_message(m.chat.id, m.message_id - i)
            deleted += 1
        except:
            continue
    bot.reply_to(m, f"🧹 {deleted} پیام پاک شد")

@bot.message_handler(func=lambda m:(is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)) and cmd_text(m).startswith("حذف "))
def delete_n(m):
    try:
        n = int(cmd_text(m).split()[1])
    except:
        return bot.reply_to(m, "❗ فرمت درست: حذف 10")
    deleted = 0
    for i in range(1, n+1):
        try:
            bot.delete_message(m.chat.id, m.message_id - i)
            deleted += 1
        except:
            continue
    bot.reply_to(m, f"🗑 {deleted} پیام پاک شد")

# ================== 🔒 قفل‌ها (لینک و گروه) ==================
@bot.message_handler(func=lambda m: cmd_text(m) in ["قفل لینک", "بازکردن لینک"])
def lock_link(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    data = load_data(); gid = str(m.chat.id)
    data["locks"].setdefault(gid, {"link": False, "group": False})
    en = (cmd_text(m) == "قفل لینک")
    data["locks"][gid]["link"] = en
    save_data(data)
    bot.reply_to(m, "🔒 قفل لینک فعال شد" if en else "🔓 قفل لینک غیرفعال شد")

@bot.message_handler(func=lambda m: cmd_text(m) in ["قفل گروه", "بازکردن گروه"])
def lock_group(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    data = load_data(); gid = str(m.chat.id)
    data["locks"].setdefault(gid, {"link": False, "group": False})
    en = (cmd_text(m) == "قفل گروه")
    data["locks"][gid]["group"] = en
    save_data(data)
    bot.reply_to(m, "🔒 گروه بسته شد (فقط مدیران می‌توانند پیام دهند)" if en else "🔓 گروه باز شد")

# ================== 🚧 اِعمال قفل‌ها (در انتهای فایل) ==================
@bot.message_handler(content_types=['text','photo','video','document','audio','voice','sticker','animation','video_note'])
def enforce_rules(m):
    # ثبت گروه
    register_group(m.chat.id)

    # مدیر و سودو مصون
    if is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id):
        return

    data = load_data(); gid = str(m.chat.id)
    locks = data["locks"].get(gid, {"link": False, "group": False})

    # قفل گروه: حذف هر پیامی از کاربران عادی
    if locks.get("group"):
        try: bot.delete_message(m.chat.id, m.message_id)
        except: pass
        return

    # قفل لینک: چک متن یا کپشن
    txt = (m.text or "") + " " + (getattr(m, "caption", "") or "")
    if locks.get("link") and ("http://" in txt or "https://" in txt or "t.me/" in txt or "telegram.me/" in txt):
        try:
            bot.delete_message(m.chat.id, m.message_id)
            # پیام اطلاع‌رسانی (اختیاری)
            # bot.send_message(m.chat.id, "🚫 ارسال لینک ممنوع است!", reply_to_message_id=m.message_id)
        except:
            pass

# ================== 🚀 اجرای ربات ==================
print("🤖 Bot is running...")
bot.infinity_polling(timeout=60, long_polling_timeout=30)
