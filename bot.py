# -*- coding: utf-8 -*-
import os
import json
import random
from datetime import datetime, timedelta
import pytz
import telebot
from telebot import types

# ================== تنظیمات ==================
TOKEN = os.environ.get("BOT_TOKEN") or "توکن_ربات_اینجا"
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))  # آیدی عددی خودت در Heroku یا محیط
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
sudo_ids = {SUDO_ID}

DATA_FILE = "data.json"
# فایل داده را آماده کن
if not os.path.exists(DATA_FILE):
    data = {"admins": [], "sudos": list(sudo_ids), "groups": {}, "welcome": {}, "autolock": {}}
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ================== توابع کمکی ==================
def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_sudo(uid):
    return uid in sudo_ids

def is_admin(chat_id, user_id):
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator", "creator")
    except:
        return False

def cmd_text(m):
    return (getattr(m, "text", None) or "").strip()

def register_group(chat_id):
    data = load_data()
    if str(chat_id) not in data["groups"]:
        data["groups"][str(chat_id)] = True
        save_data(data)

def now_tehran():
    tz = pytz.timezone("Asia/Tehran")
    return datetime.now(tz).strftime("%H:%M (%Y-%m-%d)")

# ================== عمومی ==================
@bot.message_handler(func=lambda m: cmd_text(m) == "ساعت")
def cmd_time(m):
    bot.reply_to(m, f"🕓 ساعت تهران: {now_tehran()}")

@bot.message_handler(func=lambda m: cmd_text(m) in ["آیدی", "ایدی"])
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

SUDO_RESPONSES = ["جونم قربان 😎", "در خدمتم ✌️", "ربات آماده‌ست 🚀", "چه خبر رئیس؟ 🤖"]
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ربات")
def cmd_sudo(m):
    bot.reply_to(m, random.choice(SUDO_RESPONSES))

# ================== تفریحی: جوک و فال ==================
jokes = []
fortunes = []

def save_item(arr, m):
    if not m.reply_to_message:
        return
    if m.reply_to_message.text:
        arr.append({"type": "text", "content": m.reply_to_message.text})
    elif m.reply_to_message.photo:
        arr.append({"type": "photo", "file": m.reply_to_message.photo[-1].file_id, "caption": m.reply_to_message.caption or ""})

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ثبت جوک")
def add_joke(m):
    save_item(jokes, m)
    bot.reply_to(m, "😂 جوک ذخیره شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "جوک")
def send_joke(m):
    if not jokes:
        return bot.reply_to(m, "❗ هنوز جوکی ثبت نشده.")
    j = random.choice(jokes)
    if j["type"] == "text":
        bot.send_message(m.chat.id, j["content"])
    else:
        bot.send_photo(m.chat.id, j["file"], caption=j["caption"])

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "لیست جوک")
def list_joke(m):
    if not jokes:
        return bot.reply_to(m, "❗ لیست جوک خالی است.")
    txt = "\n".join([f"{i+1}. {(j['content'][:40] if j['type']=='text' else '[عکس]')}" for i,j in enumerate(jokes)])
    bot.reply_to(m, "😂 لیست جوک:\n"+txt)

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).startswith("حذف جوک "))
def del_joke(m):
    try:
        idx = int(cmd_text(m).split()[2]) - 1
        if 0 <= idx < len(jokes):
            jokes.pop(idx)
            bot.reply_to(m, "✅ جوک حذف شد.")
        else:
            bot.reply_to(m, "❗ شماره نامعتبر.")
    except:
        bot.reply_to(m, "❗ فرمت: حذف جوک 2")

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ثبت فال")
def add_fal(m):
    save_item(fortunes, m)
    bot.reply_to(m, "🔮 فال ذخیره شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "فال")
def send_fal(m):
    if not fortunes:
        return bot.reply_to(m, "❗ هنوز فالی ثبت نشده.")
    f = random.choice(fortunes)
    if f["type"] == "text":
        bot.send_message(m.chat.id, f["content"])
    else:
        bot.send_photo(m.chat.id, f["file"], caption=f["caption"])

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "لیست فال")
def list_fal(m):
    if not fortunes:
        return bot.reply_to(m, "❗ لیست فال خالی است.")
    txt = "\n".join([f"{i+1}. {(f['content'][:40] if f['type']=='text' else '[عکس]')}" for i,f in enumerate(fortunes)])
    bot.reply_to(m, "🔮 لیست فال:\n"+txt)

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).startswith("حذف فال "))
def del_fal(m):
    try:
        idx = int(cmd_text(m).split()[2]) - 1
        if 0 <= idx < len(fortunes):
            fortunes.pop(idx)
            bot.reply_to(m, "✅ فال حذف شد.")
        else:
            bot.reply_to(m, "❗ شماره نامعتبر.")
    except:
        bot.reply_to(m, "❗ فرمت: حذف فال 2")

# ================== خوشامد خودکار ==================
@bot.message_handler(content_types=["new_chat_members"])
def welcome_new_member(m):
    try:
        register_group(m.chat.id)
        data = load_data()
        group = str(m.chat.id)
        settings = data["welcome"].get(group, {"enabled": True, "type": "text", "content": None})
        if not settings.get("enabled", True):
            return
        name = m.new_chat_members[0].first_name
        time_str = now_tehran()
        # default message (همون قالبی که خواستی)
        default_text = (f"سلام عزیز\n"
                        f"به گروه خوش آمدید 😎\n\n"
                        f"ساعت ›› {time_str}")
        text = settings.get("content") or default_text
        text = text.replace("{name}", name).replace("{time}", time_str)
        if settings.get("type") == "photo" and settings.get("file_id"):
            bot.send_photo(m.chat.id, settings["file_id"], caption=text)
        else:
            bot.send_message(m.chat.id, text)
    except Exception as e:
        print("welcome error:", e)

@bot.message_handler(func=lambda m: cmd_text(m) in ["خوشامد روشن", "خوشامد خاموش"])
def toggle_welcome(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)):
        return
    data = load_data()
    group = str(m.chat.id)
    en = (cmd_text(m) == "خوشامد روشن")
    data["welcome"].setdefault(group, {"enabled": True})
    data["welcome"][group]["enabled"] = en
    save_data(data)
    bot.reply_to(m, "✅ خوشامد روشن شد" if en else "🚫 خوشامد خاموش شد")

@bot.message_handler(func=lambda m: cmd_text(m) == "تنظیم خوشامد متن" and m.reply_to_message)
def set_welcome_text(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    data = load_data()
    group = str(m.chat.id)
    txt = m.reply_to_message.text or ""
    data["welcome"][group] = {"enabled": True, "type": "text", "content": txt}
    save_data(data)
    bot.reply_to(m, "📝 متن خوشامد تنظیم شد. می‌تونی از {name} و {time} استفاده کنی.")

@bot.message_handler(func=lambda m: cmd_text(m) == "تنظیم خوشامد عکس" and m.reply_to_message and m.reply_to_message.photo)
def set_welcome_photo(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    data = load_data()
    group = str(m.chat.id)
    fid = m.reply_to_message.photo[-1].file_id
    caption = m.reply_to_message.caption or "خوش آمدی {name}"
    data["welcome"][group] = {"enabled": True, "type": "photo", "file_id": fid, "content": caption}
    save_data(data)
    bot.reply_to(m, "🖼 خوشامد تصویری تنظیم شد.")

# ================== قفل‌ها ==================
locks = {k: {} for k in ["links", "stickers", "photo", "video", "gif", "file", "music", "voice", "forward"]}
LOCK_MAP = {
    "لینک": "links", "استیکر": "stickers", "عکس": "photo", "ویدیو": "video",
    "گیف": "gif", "فایل": "file", "موزیک": "music", "ویس": "voice", "فوروارد": "forward"
}
group_lock = {}
# autolock stored in data['autolock'] per group; toggle command below

@bot.message_handler(func=lambda m: cmd_text(m).startswith("قفل "))
def cmd_lock(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    k = cmd_text(m).replace("قفل ", "", 1)
    if k == "گروه":
        group_lock[m.chat.id] = True
        return bot.reply_to(m, "🔒 گروه بسته شد — کاربران عادی نمی‌توانند پیام ارسال کنند.")
    key = LOCK_MAP.get(k)
    if key:
        locks[key][m.chat.id] = True
        bot.reply_to(m, f"🔒 قفل {k} فعال شد.")
    else:
        bot.reply_to(m, "❗ نوع قفل نامشخص است.")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("باز کردن "))
def cmd_unlock(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    k = cmd_text(m).replace("باز کردن ", "", 1)
    if k == "گروه":
        group_lock[m.chat.id] = False
        return bot.reply_to(m, "🔓 گروه باز شد.")
    key = LOCK_MAP.get(k)
    if key:
        locks[key][m.chat.id] = False
        bot.reply_to(m, f"🔓 قفل {k} باز شد.")
    else:
        bot.reply_to(m, "❗ نوع قفل نامشخص است.")

@bot.message_handler(func=lambda m: cmd_text(m) == "قفل خودکار")
def cmd_autolock(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    data = load_data()
    auto = data.get("autolock", {})
    key = str(m.chat.id)
    new = not auto.get(key, False)
    auto[key] = new
    data["autolock"] = auto
    save_data(data)
    bot.reply_to(m, "🕔 قفل خودکار فعال شد." if new else "🚫 قفل خودکار غیرفعال شد.")

# اعمال قفل‌ها بر پیام‌ها
@bot.message_handler(content_types=['text','photo','video','document','audio','voice','sticker','animation'])
def enforce_locks(m):
    register_group(m.chat.id)
    # مدیران و سودوها نادیده گرفته شوند
    if is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id):
        return
    txt = m.text or ""
    # قفل کل گروه
    if group_lock.get(m.chat.id):
        try:
            bot.delete_message(m.chat.id, m.message_id)
        except:
            pass
        return
    # بقیه قفل‌ها
    try:
        if locks["links"].get(m.chat.id) and any(x in txt for x in ["http://","https://","t.me","telegram.me"]):
            bot.delete_message(m.chat.id, m.message_id)
        if locks["stickers"].get(m.chat.id) and m.sticker:
            bot.delete_message(m.chat.id, m.message_id)
        if locks["photo"].get(m.chat.id) and m.photo:
            bot.delete_message(m.chat.id, m.message_id)
        if locks["video"].get(m.chat.id) and m.video:
            bot.delete_message(m.chat.id, m.message_id)
        if locks["gif"].get(m.chat.id) and m.animation:
            bot.delete_message(m.chat.id, m.message_id)
        if locks["file"].get(m.chat.id) and m.document:
            bot.delete_message(m.chat.id, m.message_id)
        if locks["music"].get(m.chat.id) and m.audio:
            bot.delete_message(m.chat.id, m.message_id)
        if locks["voice"].get(m.chat.id) and m.voice:
            bot.delete_message(m.chat.id, m.message_id)
        if locks["forward"].get(m.chat.id) and (m.forward_from or m.forward_from_chat):
            bot.delete_message(m.chat.id, m.message_id)
    except:
        pass

# ================== پن (pin) ==================
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "پن")
def cmd_pin(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    try:
        bot.pin_chat_message(m.chat.id, m.reply_to_message.message_id)
        bot.reply_to(m, "📌 پیام پین شد.")
    except Exception as e:
        bot.reply_to(m, "❗ خطا در پین پیام.")

@bot.message_handler(func=lambda m: cmd_text(m) == "حذف پن")
def cmd_unpin(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    try:
        bot.unpin_all_chat_messages(m.chat.id)
        bot.reply_to(m, "🧹 همه پیام‌های پین حذف شد.")
    except:
        bot.reply_to(m, "❗ خطا در حذف پن.")

# ================== بن / سکوت / اخطار ==================
banned = {}
muted = {}
warnings = {}
MAX_WARNINGS = 3

def protect_user(chat_id, uid):
    if is_sudo(uid):
        return "⚡ این کاربر سودو است"
    try:
        member = bot.get_chat_member(chat_id, uid)
        if member.status == "creator":
            return "❗ صاحب گروه قابل مدیریت نیست"
    except:
        pass
    return None

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "بن")
def cmd_ban(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    prot = protect_user(m.chat.id, uid)
    if prot:
        return bot.reply_to(m, prot)
    try:
        bot.ban_chat_member(m.chat.id, uid)
        banned.setdefault(m.chat.id, set()).add(uid)
        bot.reply_to(m, "🚫 کاربر بن شد.")
    except:
        bot.reply_to(m, "❗ خطا در بن کاربر.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف بن")
def cmd_unban(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    try:
        bot.unban_chat_member(m.chat.id, uid)
        banned.get(m.chat.id, set()).discard(uid)
        bot.reply_to(m, "✅ بن حذف شد.")
    except:
        bot.reply_to(m, "❗ خطا در حذف بن.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "سکوت")
def cmd_mute(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    prot = protect_user(m.chat.id, uid)
    if prot:
        return bot.reply_to(m, prot)
    try:
        bot.restrict_chat_member(m.chat.id, uid, can_send_messages=False)
        muted.setdefault(m.chat.id, set()).add(uid)
        bot.reply_to(m, "🔕 کاربر در سکوت قرار گرفت.")
    except:
        bot.reply_to(m, "❗ خطا در سکوت کاربران.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف سکوت")
def cmd_unmute(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    try:
        bot.restrict_chat_member(m.chat.id, uid,
                                can_send_messages=True, can_send_media_messages=True,
                                can_send_other_messages=True, can_add_web_page_previews=True)
        muted.get(m.chat.id, set()).discard(uid)
        bot.reply_to(m, "🔊 سکوت کاربر حذف شد.")
    except:
        bot.reply_to(m, "❗ خطا در حذف سکوت.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "اخطار")
def cmd_warn(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    prot = protect_user(m.chat.id, uid)
    if prot:
        return bot.reply_to(m, prot)
    warnings.setdefault(m.chat.id, {})
    warnings[m.chat.id][uid] = warnings[m.chat.id].get(uid, 0) + 1
    c = warnings[m.chat.id][uid]
    if c >= MAX_WARNINGS:
        try:
            bot.ban_chat_member(m.chat.id, uid)
            warnings[m.chat.id][uid] = 0
            bot.reply_to(m, "🚫 کاربر با ۳ اخطار بن شد.")
        except:
            bot.reply_to(m, "❗ خطا در بن با اخطار.")
    else:
        bot.reply_to(m, f"⚠️ اخطار {c}/{MAX_WARNINGS}")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف اخطار")
def cmd_reset_warn(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    warnings.get(m.chat.id, {}).pop(uid, None)
    bot.reply_to(m, "✅ اخطارها حذف شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست بن")
def cmd_list_ban(m):
    ids = banned.get(m.chat.id, set())
    if not ids:
        return bot.reply_to(m, "❗ لیست بن خالی است.")
    txt = "\n".join([f"▪️ {i}" for i in ids])
    bot.reply_to(m, "🚫 لیست بن:\n" + txt)

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست سکوت")
def cmd_list_mute(m):
    ids = muted.get(m.chat.id, set())
    if not ids:
        return bot.reply_to(m, "❗ لیست سکوت خالی است.")
    txt = "\n".join([f"▪️ {i}" for i in ids])
    bot.reply_to(m, "🔕 لیست سکوت:\n" + txt)

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست اخطار")
def cmd_list_warn(m):
    ws = warnings.get(m.chat.id, {})
    if not ws:
        return bot.reply_to(m, "❗ لیست اخطار خالی است.")
    txt = "\n".join([f"▪️ {uid} — {c} اخطار" for uid, c in ws.items()])
    bot.reply_to(m, "⚠️ لیست اخطار:\n" + txt)

# ================== پاکسازی ==================
@bot.message_handler(func=lambda m: (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)) and cmd_text(m) == "پاکسازی")
def cmd_clear_all(m):
    deleted = 0
    try:
        for i in range(1, 201):
            bot.delete_message(m.chat.id, m.message_id - i)
            deleted += 1
    except:
        pass
    bot.reply_to(m, f"🧹 {deleted} پیام پاک شد.")

@bot.message_handler(func=lambda m: (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)) and cmd_text(m).startswith("حذف "))
def cmd_delete_n(m):
    try:
        n = int(cmd_text(m).split()[1])
        deleted = 0
        for i in range(1, n + 1):
            bot.delete_message(m.chat.id, m.message_id - i)
            deleted += 1
        bot.reply_to(m, f"🗑 {deleted} پیام پاک شد.")
    except:
        bot.reply_to(m, "❗ فرمت درست: حذف 10")

# ================== ارسال همگانی ==================
waiting_for_broadcast = {}

@bot.message_handler(func=lambda m: cmd_text(m) == "ارسال همگانی")
def ask_broadcast(m):
    if not is_sudo(m.from_user.id):
        return
    waiting_for_broadcast[m.from_user.id] = True
    bot.reply_to(m, "📝 لطفاً متن پیام همگانی را ارسال کن:")

@bot.message_handler(func=lambda m: m.from_user.id in waiting_for_broadcast)
def do_broadcast(m):
    if not is_sudo(m.from_user.id): return
    text = m.text or ""
    waiting_for_broadcast.pop(m.from_user.id, None)
    data = load_data()
    groups = data.get("groups", {})
    sent = 0
    for gid in groups.keys():
        try:
            bot.send_message(int(gid), f"📢 پیام همگانی:\n{text}")
            sent += 1
        except:
            pass
    bot.reply_to(m, f"✅ پیام به {sent} گروه ارسال شد.")

# ================== مدیریت مدیران و سودو ==================
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "افزودن مدیر")
def add_admin_cmd(m):
    if not is_sudo(m.from_user.id): return
    data = load_data()
    uid = m.reply_to_message.from_user.id
    if uid not in data["admins"]:
        data["admins"].append(uid)
        save_data(data)
        bot.reply_to(m, "👮 مدیر اضافه شد.")
    else:
        bot.reply_to(m, "❗ این کاربر از قبل مدیر است.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف مدیر")
def del_admin_cmd(m):
    if not is_sudo(m.from_user.id): return
    data = load_data()
    uid = m.reply_to_message.from_user.id
    if uid in data["admins"]:
        data["admins"].remove(uid)
        save_data(data)
        bot.reply_to(m, "🚫 مدیر حذف شد.")
    else:
        bot.reply_to(m, "❗ این کاربر مدیر نیست.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست مدیران")
def list_admins_cmd(m):
    if not is_sudo(m.from_user.id): return
    data = load_data()
    if not data["admins"]:
        return bot.reply_to(m, "❗ هیچ مدیری ثبت نشده.")
    txt = "\n".join([f"▪️ {uid}" for uid in data["admins"]])
    bot.reply_to(m, "👮 لیست مدیران:\n" + txt)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "افزودن سودو")
def add_sudo_cmd(m):
    if not is_sudo(m.from_user.id): return
    data = load_data()
    uid = m.reply_to_message.from_user.id
    if uid not in data["sudos"]:
        data["sudos"].append(uid)
        save_data(data)
        sudo_ids.add(uid)
        bot.reply_to(m, "⚡ سودو اضافه شد.")
    else:
        bot.reply_to(m, "❗ این کاربر سودو است.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف سودو")
def del_sudo_cmd(m):
    if not is_sudo(m.from_user.id): return
    data = load_data()
    uid = m.reply_to_message.from_user.id
    if uid in data["sudos"]:
        data["sudos"].remove(uid)
        save_data(data)
        sudo_ids.discard(uid)
        bot.reply_to(m, "🚫 سودو حذف شد.")
    else:
        bot.reply_to(m, "❗ این کاربر سودو نیست.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست سودو")
def list_sudos_cmd(m):
    if not is_sudo(m.from_user.id): return
    data = load_data()
    if not data["sudos"]:
        return bot.reply_to(m, "❗ هیچ سودویی ثبت نشده.")
    txt = "\n".join([f"▪️ {uid}" for uid in data["sudos"]])
    bot.reply_to(m, "⚡ لیست سودوها:\n" + txt)

# ================== پنل اینلاین ==================
@bot.message_handler(func=lambda m: cmd_text(m) == "پنل")
def panel_cmd(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🎉 خوشامد", callback_data="panel_welcome"),
           types.InlineKeyboardButton("📎 لینک", callback_data="panel_link"))
    kb.add(types.InlineKeyboardButton("📌 پن", callback_data="panel_pin"),
           types.InlineKeyboardButton("✉️ ارسال همگانی", callback_data="panel_broadcast"))
    kb.add(types.InlineKeyboardButton("👮 مدیریت", callback_data="panel_admins"),
           types.InlineKeyboardButton("📘 راهنما", callback_data="panel_help"))
    bot.send_message(m.chat.id, "🧭 پنل مدیریت:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "panel_help")
def cb_help(c):
    text = ("📘 <b>راهنما:</b>\n\n"
            "• عمومی: ساعت / آیدی\n"
            "• تفریحی: جوک / فال (ثبت فقط برای سودو)\n"
            "• مدریتی: بن / حذف بن / سکوت / حذف سکوت / اخطار / حذف اخطار / پاکسازی / حذف [عدد]\n"
            "• قفل‌ها: قفل [نوع] / باز کردن [نوع] / قفل گروه / قفل خودکار\n"
            "• خوشامد: خوشامد روشن/خاموش / تنظیم خوشامد متن / تنظیم خوشامد عکس\n"
            "• سودو: ارسال همگانی / افزودن/حذف مدیر / افزودن/حذف سودو\n")
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode="HTML")
    except:
        pass

@bot.callback_query_handler(func=lambda c: c.data == "panel_link")
def cb_link(c):
    fake = types.SimpleNamespace(chat=c.message.chat, from_user=c.from_user, text="لینک")
    get_link(fake)

@bot.callback_query_handler(func=lambda c: c.data == "panel_welcome")
def cb_welcome(c):
    bot.answer_callback_query(c.id, "برای خوشامد از دستورات:\n«تنظیم خوشامد متن» یا «تنظیم خوشامد عکس» استفاده کنید.", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data == "panel_pin")
def cb_pin(c):
    bot.answer_callback_query(c.id, "برای پین پیام از دستور «پن» استفاده کن (باید به یک پیام ریپلای کنی).", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data == "panel_broadcast")
def cb_broadcast(c):
    fake = types.SimpleNamespace(chat=c.message.chat, from_user=c.from_user, text="ارسال همگانی")
    ask_broadcast(fake)

@bot.callback_query_handler(func=lambda c: c.data == "panel_admins")
def cb_admins(c):
    fake = types.SimpleNamespace(chat=c.message.chat, from_user=c.from_user, text="لیست مدیران")
    list_admins_cmd(fake)

# ================== ثبت گروه هنگام هر پیام ==================
@bot.message_handler(func=lambda m: True, content_types=['text','photo','video','document','audio','voice','sticker','animation'])
def register_on_message(m):
    register_group(m.chat.id)
    # بقیه پردازش‌ها در هندلرهای مخصوص انجام می‌شود
    return

# ================== اجرای ربات ==================
if __name__ == "__main__":
    print("🤖 Bot is running...")
    bot.infinity_polling(skip_pending=True, timeout=30)
