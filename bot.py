# -*- coding: utf-8 -*-
import os, json, random
from datetime import datetime
import pytz, jdatetime
import telebot
from telebot import types

# ================== ⚙️ تنظیمات ==================
TOKEN   = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
sudo_ids = {SUDO_ID}
DATA_FILE = "data.json"

# ================== 📂 فایل دیتا ==================
def base_data():
    return {
        "welcome": {},
        "locks": {},
        "banned": {},
        "muted": {},
        "admins": {},
        "users": []  # لیست؛ نه set
    }

def _normalize(o):
    """هر set را به list تبدیل می‌کند (حتی به صورت تو در تو)."""
    if isinstance(o, set):
        return list(o)
    if isinstance(o, dict):
        return {k: _normalize(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_normalize(i) for i in o]
    return o

def load_data():
    base = base_data()
    if not os.path.exists(DATA_FILE):
        save_data(base)
        return base
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        data = base
    for k in base:
        if k not in data:
            data[k] = base[k]
    # اگر نسخه‌های قبلی set ذخیره کرده باشند، همین‌جا نرمال می‌کنیم
    save_data(data)
    return data

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(_normalize(d), f, ensure_ascii=False, indent=2)

def register_group(gid):
    data = load_data()
    gid = str(gid)
    data["welcome"].setdefault(gid, {"enabled": True, "type": "text", "content": None})
    data["locks"].setdefault(gid, {
        k: False for k in ["link","group","photo","video","sticker","gif","file","music","voice","forward"]
    })
    save_data(data)

# ================== 🧩 کمکی ==================
def is_sudo(uid): return uid in sudo_ids
def is_admin(chat_id, uid):
    data = load_data()
    gid = str(chat_id)
    if uid in sudo_ids: return True
    if str(uid) in data["admins"].get(gid, []): return True
    try:
        st = bot.get_chat_member(chat_id, uid).status
        return st in ("administrator", "creator")
    except:
        return False

def cmd_text(m): return (getattr(m, "text", None) or "").strip()
def now_teh(): return datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
def now_shamsi(): return jdatetime.datetime.now().strftime("%H:%M (%A %d %B %Y)")

# ================== 👑 مدیریت مدیران ==================
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "افزودن مدیر")
def add_admin(m):
    if not is_sudo(m.from_user.id): return
    data = load_data(); gid = str(m.chat.id)
    uid = str(m.reply_to_message.from_user.id)
    data["admins"].setdefault(gid, [])
    if uid not in data["admins"][gid]:
        data["admins"][gid].append(uid)
        save_data(data)
        bot.reply_to(m, f"✅ {uid} به لیست مدیران افزوده شد.")
    else:
        bot.reply_to(m, "⚠️ این کاربر از قبل مدیر است.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف مدیر")
def remove_admin(m):
    if not is_sudo(m.from_user.id): return
    data = load_data(); gid = str(m.chat.id)
    uid = str(m.reply_to_message.from_user.id)
    if uid in data["admins"].get(gid, []):
        data["admins"][gid].remove(uid)
        save_data(data)
        bot.reply_to(m, f"🗑 مدیر {uid} حذف شد.")
    else:
        bot.reply_to(m, "❌ این کاربر مدیر نیست.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست مدیران")
def list_admins(m):
    data = load_data(); gid = str(m.chat.id)
    lst = data["admins"].get(gid, [])
    if not lst:
        return bot.reply_to(m, "❗ هیچ مدیری ثبت نشده.")
    txt = "\n".join([f"• {i}" for i in lst])
    bot.reply_to(m, "👑 لیست مدیران:\n" + txt)

# ================== 💬 دستورات عمومی ==================
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

@bot.message_handler(func=lambda m: cmd_text(m) == "ساعت")
def cmd_time(m):
    bot.reply_to(m, f"⏰ تهران: {now_teh()}\n📅 شمسی: {now_shamsi()}")

@bot.message_handler(func=lambda m: cmd_text(m) == "آمار")
def cmd_stats(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        count = bot.get_chat_member_count(m.chat.id)
    except: count = "نامشخص"
    bot.reply_to(m, f"📊 اعضای گروه: {count}")

# ================== 🤖 ثبت کاربران ==================
@bot.message_handler(commands=["start"])
def start_cmd(m):
    data = load_data()
    users = set(data.get("users", []))
    users.add(m.from_user.id)
    data["users"] = list(users)
    save_data(data)
    bot.reply_to(m, "سلام 👋 ربات مدیریتی فعال است.")

# ================== 🎉 خوشامد ==================
@bot.message_handler(content_types=["new_chat_members"])
def welcome(m):
    register_group(m.chat.id)
    data = load_data()
    gid = str(m.chat.id)
    s = data["welcome"].get(gid, {"enabled": True, "type": "text", "content": None})
    if not s.get("enabled", True): return
    name = m.new_chat_members[0].first_name or "دوست جدید"
    t = now_shamsi()
    text = s.get("content") or f"سلام {name} 🌙\nبه گروه {m.chat.title} خوش اومدی 😎\n⏰ {t}"
    bot.send_message(m.chat.id, text)

@bot.message_handler(func=lambda m: cmd_text(m) in ["خوشامد روشن","خوشامد خاموش"])
def toggle_welcome(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    data = load_data(); gid = str(m.chat.id)
    en = cmd_text(m) == "خوشامد روشن"
    data["welcome"].setdefault(gid, {"enabled": True})
    data["welcome"][gid]["enabled"] = en
    save_data(data)
    bot.reply_to(m, "✅ خوشامد روشن شد" if en else "🚫 خوشامد خاموش شد")

@bot.message_handler(func=lambda m: cmd_text(m) == "تنظیم خوشامد" and m.reply_to_message)
def set_welcome(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    data = load_data(); gid = str(m.chat.id)
    txt = (m.reply_to_message.text or "").strip()
    data["welcome"][gid] = {"enabled": True, "type": "text", "content": txt}
    save_data(data)
    bot.reply_to(m, "📝 متن خوشامد تنظیم شد.")

# ================== 🔨 بن و سکوت ==================
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "بن")
def ban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    try:
        bot.ban_chat_member(m.chat.id, uid)
        bot.reply_to(m, f"🚫 کاربر {uid} بن شد.")
    except Exception as e:
        bot.reply_to(m, f"❗ خطا در بن: {e}")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف بن")
def unban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    try:
        bot.unban_chat_member(m.chat.id, uid, only_if_banned=True)
        bot.reply_to(m, "✅ بن حذف شد.")
    except Exception as e:
        bot.reply_to(m, f"❗ خطا در حذف بن: {e}")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "سکوت")
def mute_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    try:
        perms = types.ChatPermissions(can_send_messages=False)
        bot.restrict_chat_member(m.chat.id, uid, permissions=perms)
        bot.reply_to(m, f"🔇 کاربر {uid} در سکوت قرار گرفت.")
    except Exception as e:
        bot.reply_to(m, f"❗ خطا در سکوت: {e}")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف سکوت")
def unmute_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    try:
        perms = types.ChatPermissions(can_send_messages=True)
        bot.restrict_chat_member(m.chat.id, uid, permissions=perms)
        bot.reply_to(m, "🔊 سکوت حذف شد.")
    except Exception as e:
        bot.reply_to(m, f"❗ خطا در حذف سکوت: {e}")

# ================== 🧹 پاکسازی ==================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "پاکسازی")
def clear(m):
    deleted = 0
    for i in range(1, 101):
        try:
            bot.delete_message(m.chat.id, m.message_id - i)
            deleted += 1
        except: continue
    bot.reply_to(m, f"🧹 {deleted} پیام پاک شد.")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("حذف "))
def delete_n(m):
    try:
        n = int(cmd_text(m).split()[1])
    except:
        return bot.reply_to(m, "❗ فرمت درست: حذف 10")
    deleted = 0
    for i in range(1, n + 1):
        try:
            bot.delete_message(m.chat.id, m.message_id - i)
            deleted += 1
        except: continue
    bot.reply_to(m, f"🗑 {deleted} پیام پاک شد.")

# ================== 🔒 قفل‌ها ==================
@bot.message_handler(func=lambda m: cmd_text(m).startswith("قفل ") or cmd_text(m).startswith("بازکردن "))
def toggle_lock(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    data = load_data(); gid = str(m.chat.id)
    part = cmd_text(m).split(" ")
    if len(part) < 2: return
    lock_type = part[1]
    en = cmd_text(m).startswith("قفل ")
    data["locks"].setdefault(gid, {k: False for k in ["link","group","photo","video","sticker","gif","file","music","voice","forward"]})
    if lock_type not in data["locks"][gid]:
        return bot.reply_to(m, "❌ نوع قفل نامعتبر است.")
    data["locks"][gid][lock_type] = en
    save_data(data)
    bot.reply_to(m, f"🔒 قفل {lock_type} فعال شد" if en else f"🔓 قفل {lock_type} غیرفعال شد")

@bot.message_handler(content_types=['text','photo','video','document','audio','voice','sticker','animation','video_note'])
def enforce(m):
    register_group(m.chat.id)
    if is_admin(m.chat.id, m.from_user.id): return
    data = load_data(); gid = str(m.chat.id)
    locks = data["locks"].get(gid, {})
    if locks.get("group"):
        try: bot.delete_message(m.chat.id, m.message_id)
        except: pass
        return
    txt = (m.text or "") + " " + (getattr(m, "caption", "") or "")
    if locks.get("link") and any(x in txt for x in ["http://","https://","t.me","telegram.me"]):
        try: bot.delete_message(m.chat.id, m.message_id)
        except: pass
        return
    if locks.get("sticker") and m.sticker: bot.delete_message(m.chat.id, m.message_id)
    if locks.get("photo") and m.photo: bot.delete_message(m.chat.id, m.message_id)
    if locks.get("video") and m.video: bot.delete_message(m.chat.id, m.message_id)
    if locks.get("gif") and m.animation: bot.delete_message(m.chat.id, m.message_id)
    if locks.get("file") and m.document: bot.delete_message(m.chat.id, m.message_id)
    if locks.get("music") and m.audio: bot.delete_message(m.chat.id, m.message_id)
    if locks.get("voice") and m.voice: bot.delete_message(m.chat.id, m.message_id)
    if locks.get("forward") and (m.forward_from or m.forward_from_chat): bot.delete_message(m.chat.id, m.message_id)

# ================== 😂 جوک و 🔮 فال ==================
jokes, falls = [], []

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ثبت جوک" and m.reply_to_message)
def add_joke(m):
    jokes.append(m.reply_to_message.text)
    bot.reply_to(m, "😂 جوک ذخیره شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "جوک")
def send_joke(m):
    if not jokes: return bot.reply_to(m, "❗ جوکی ثبت نشده.")
    bot.reply_to(m, random.choice(jokes))

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ثبت فال" and m.reply_to_message)
def add_fal(m):
    falls.append(m.reply_to_message.text)
    bot.reply_to(m, "🔮 فال ذخیره شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "فال")
def send_fal(m):
    if not falls: return bot.reply_to(m, "❗ فالی ثبت نشده.")
    bot.reply_to(m, random.choice(falls))

# ================== 📢 ارسال همگانی ==================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ارسال" and m.reply_to_message)
def broadcast(m):
    data = load_data()
    users = list(set(data.get("users", [])))
    groups = [int(g) for g in data.get("welcome", {}).keys()]  # آی‌دی گروه‌ها حتماً int
    targets = users + groups
    total = 0
    msg = m.reply_to_message
    for uid in targets:
        try:
            if msg.text:
                bot.send_message(uid, msg.text)
            elif msg.photo:
                bot.send_photo(uid, msg.photo[-1].file_id, caption=msg.caption or "")
            total += 1
        except:
            continue
    bot.reply_to(m, f"📢 پیام به {total} کاربر ارسال شد.")

# ================== 🚀 اجرای ربات ==================
print("🤖 Bot is running...")
bot.infinity_polling(timeout=60, long_polling_timeout=30)
