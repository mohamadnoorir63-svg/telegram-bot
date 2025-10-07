# -*- coding: utf-8 -*-
import os, random
from datetime import datetime
import pytz
import telebot

# ================== ⚙️ تنظیمات ==================
TOKEN   = os.environ.get("BOT_TOKEN") or "توکن_ربات_اینجا"
SUDO_ID = int(os.environ.get("SUDO_ID", "123456789"))  # آیدی عددی خودت

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
sudo_ids = {SUDO_ID}

# ================== 🧩 کمکی ==================
def is_sudo(uid): 
    return uid in sudo_ids

def is_admin(chat_id, user_id):
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator","creator")
    except:
        return False

def cmd_text(m):
    return (getattr(m, "text", None) or "").strip()

# ================== 💬 دستورات عمومی ==================
@bot.message_handler(func=lambda m: cmd_text(m)=="ساعت")
def cmd_time(m):
    now_utc = datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
    now_teh = datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
    bot.reply_to(m, f"⏰ UTC: {now_utc}\n🕓 تهران: {now_teh}")

@bot.message_handler(func=lambda m: cmd_text(m)=="آمار")
def cmd_stats(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    try: count = bot.get_chat_member_count(m.chat.id)
    except: count = "نامشخص"
    bot.reply_to(m, f"📊 اعضای گروه: {count}")

@bot.message_handler(func=lambda m: cmd_text(m)=="ایدی")
def cmd_id(m):
    caption = f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 گروه: <code>{m.chat.id}</code>"
    try:
        photos = bot.get_user_profile_photos(m.from_user.id, limit=1)
        if photos.total_count>0:
            bot.send_photo(m.chat.id, photos.photos[0][-1].file_id, caption=caption)
        else:
            bot.reply_to(m, caption)
    except:
        bot.reply_to(m, caption)

SUDO_RESPONSES = ["جونم قربان 😎","در خدمتم ✌️","ربات آماده‌ست 🚀","چه خبر رئیس؟ 🤖"]
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="ربات")
def cmd_sudo(m):
    bot.reply_to(m, random.choice(SUDO_RESPONSES))

# ================== 😂 جوک و 🔮 فال ==================
jokes = []
fortunes = []

def _save_item(arr, m):
    if not m.reply_to_message: return
    if m.reply_to_message.text:
        arr.append({"type":"text","content":m.reply_to_message.text})
    elif m.reply_to_message.photo:
        arr.append({"type":"photo","file":m.reply_to_message.photo[-1].file_id,"caption":(m.reply_to_message.caption or "")})

# جوک
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="ثبت جوک")
def add_joke(m):
    _save_item(jokes, m)
    bot.reply_to(m, "😂 جوک ذخیره شد")

@bot.message_handler(func=lambda m: cmd_text(m)=="جوک")
def send_joke(m):
    if not jokes: return bot.reply_to(m, "❗ جوکی ثبت نشده")
    j = random.choice(jokes)
    if j["type"] == "text":
        bot.send_message(m.chat.id, j["content"])
    else:
        bot.send_photo(m.chat.id, j["file"], caption=j["caption"])

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="لیست جوک")
def list_joke(m):
    if not jokes: return bot.reply_to(m, "❗ جوکی ثبت نشده")
    txt = "\n".join([f"{i+1}. {(j['content'][:40] if j['type']=='text' else '[عکس]')}" for i,j in enumerate(jokes)])
    bot.reply_to(m, "😂 لیست جوک:\n"+txt)

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).startswith("حذف جوک "))
def del_joke(m):
    try:
        idx = int(cmd_text(m).split()[2]) - 1
        if 0 <= idx < len(jokes):
            jokes.pop(idx); bot.reply_to(m, "✅ جوک حذف شد")
        else:
            bot.reply_to(m, "❗ شماره نامعتبر")
    except:
        bot.reply_to(m, "❗ فرمت: حذف جوک 2")

# فال
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="ثبت فال")
def add_fal(m):
    _save_item(fortunes, m)
    bot.reply_to(m, "🔮 فال ذخیره شد")

@bot.message_handler(func=lambda m: cmd_text(m)=="فال")
def send_fal(m):
    if not fortunes: return bot.reply_to(m, "❗ فالی ثبت نشده")
    f = random.choice(fortunes)
    if f["type"] == "text":
        bot.send_message(m.chat.id, f["content"])
    else:
        bot.send_photo(m.chat.id, f["file"], caption=f["caption"])

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="لیست فال")
def list_fal(m):
    if not fortunes: return bot.reply_to(m, "❗ فالی ثبت نشده")
    txt = "\n".join([f"{i+1}. {(f['content'][:40] if f['type']=='text' else '[عکس]')}" for i,f in enumerate(fortunes)])
    bot.reply_to(m, "🔮 لیست فال:\n"+txt)

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).startswith("حذف فال "))
def del_fal(m):
    try:
        idx = int(cmd_text(m).split()[2]) - 1
        if 0 <= idx < len(fortunes):
            fortunes.pop(idx); bot.reply_to(m, "✅ فال حذف شد")
        else:
            bot.reply_to(m, "❗ شماره نامعتبر")
    except:
        bot.reply_to(m, "❗ فرمت: حذف فال 2")

# ================== 🔒 قفل‌ها ==================
locks = {k:{} for k in ["links","stickers","bots","photo","video","gif","file","music","voice","forward"]}
LOCK_MAP = {
    "لینک":"links","استیکر":"stickers","ربات":"bots","عکس":"photo","ویدیو":"video",
    "گیف":"gif","فایل":"file","موزیک":"music","ویس":"voice","فوروارد":"forward"
}

@bot.message_handler(func=lambda m: cmd_text(m).startswith("قفل "))
def lock(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    key_fa = cmd_text(m).replace("قفل ","",1)
    key = LOCK_MAP.get(key_fa)
    if key:
        locks[key][m.chat.id] = True
        bot.reply_to(m, f"🔒 قفل {key_fa} فعال شد")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("باز کردن "))
def unlock(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    key_fa = cmd_text(m).replace("باز کردن ","",1)
    key = LOCK_MAP.get(key_fa)
    if key:
        locks[key][m.chat.id] = False
        bot.reply_to(m, f"🔓 قفل {key_fa} باز شد")

# ================== 🔐 قفل کل گروه ==================
group_lock = {}

@bot.message_handler(func=lambda m: cmd_text(m)=="قفل گروه")
def lock_group(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    group_lock[m.chat.id] = True
    bot.send_message(m.chat.id, "🔒 گروه بسته شد — کاربران عادی اجازه ارسال پیام ندارند.")

@bot.message_handler(func=lambda m: cmd_text(m)=="باز کردن گروه")
def unlock_group(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    group_lock[m.chat.id] = False
    bot.send_message(m.chat.id, "🔓 گروه باز شد — کاربران می‌توانند پیام ارسال کنند.")

# ================== 🚫 بن / سکوت / اخطار ==================
banned, muted, warnings = {}, {}, {}
MAX_WARNINGS = 3

def protect_user(chat_id, uid):
    if is_sudo(uid): return "⚡ این کاربر سودو است"
    try:
        member = bot.get_chat_member(chat_id, uid)
        if member.status == "creator": return "❗ صاحب گروه قابل مدیریت نیست"
    except:
        pass
    return None

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="بن")
def ban(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    prot = protect_user(m.chat.id, uid)
    if prot: return bot.reply_to(m, prot)
    try:
        bot.ban_chat_member(m.chat.id, uid)
        banned.setdefault(m.chat.id,set()).add(uid)
        bot.reply_to(m, "🚫 کاربر بن شد")
    except:
        bot.reply_to(m, "❗ خطا در بن")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف بن")
def unban(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    try:
        bot.unban_chat_member(m.chat.id, uid)
        banned.get(m.chat.id,set()).discard(uid)
        bot.reply_to(m, "✅ بن حذف شد")
    except:
        bot.reply_to(m, "❗ خطا در حذف بن")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="سکوت")
def mute(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    prot = protect_user(m.chat.id, uid)
    if prot: return bot.reply_to(m, prot)
    try:
        bot.restrict_chat_member(m.chat.id, uid, can_send_messages=False)
        muted.setdefault(m.chat.id,set()).add(uid)
        bot.reply_to(m, "🔕 کاربر در سکوت قرار گرفت")
    except:
        bot.reply_to(m, "❗ خطا در سکوت")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف سکوت")
def unmute(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    try:
        bot.restrict_chat_member(m.chat.id, uid,
            can_send_messages=True,can_send_media_messages=True,
            can_send_other_messages=True,can_add_web_page_previews=True)
        muted.get(m.chat.id,set()).discard(uid)
        bot.reply_to(m, "🔊 سکوت حذف شد")
    except:
        bot.reply_to(m, "❗ خطا در حذف سکوت")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="اخطار")
def warn(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    prot = protect_user(m.chat.id, uid)
    if prot: return bot.reply_to(m, prot)
    warnings.setdefault(m.chat.id, {})
    warnings[m.chat.id][uid] = warnings[m.chat.id].get(uid, 0) + 1
    c = warnings[m.chat.id][uid]
    if c >= MAX_WARNINGS:
        try:
            bot.ban_chat_member(m.chat.id, uid)
            warnings[m.chat.id][uid] = 0
            bot.reply_to(m, "🚫 کاربر با ۳ اخطار بن شد")
        except:
            bot.reply_to(m, "❗ خطا در بن با اخطار")
    else:
        bot.reply_to(m, f"⚠️ اخطار {c}/{MAX_WARNINGS}")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف اخطار")
def reset_warn(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    warnings.get(m.chat.id, {}).pop(uid, None)
    bot.reply_to(m, "✅ اخطارها حذف شد")

@bot.message_handler(func=lambda m: cmd_text(m)=="لیست اخطار")
def list_warn(m):
    ws = warnings.get(m.chat.id, {})
    if not ws: return bot.reply_to(m, "❗ لیست اخطار خالی است")
    txt = "\n".join([f"▪️ {uid} — {c} اخطار" for uid,c in ws.items()])
    bot.reply_to(m, "⚠️ لیست اخطار:\n"+txt)

# ================== 🧹 پاکسازی ==================
@bot.message_handler(func=lambda m: (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)) and cmd_text(m)=="پاکسازی")
def clear_all(m):
    deleted = 0
    try:
        for i in range(1, 201):
            bot.delete_message(m.chat.id, m.message_id - i)
            deleted += 1
    except:
        pass
    bot.reply_to(m, f"🧹 {deleted} پیام پاک شد")

@bot.message_handler(func=lambda m: (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)) and cmd_text(m).startswith("حذف "))
def delete_n(m):
    try:
        n = int(cmd_text(m).split()[1])
        deleted = 0
        for i in range(1, n+1):
            bot.delete_message(m.chat.id, m.message_id - i)
            deleted += 1
        bot.reply_to(m, f"🗑 {deleted} پیام پاک شد")
    except:
        bot.reply_to(m, "❗ فرمت درست: حذف 10")

# ================== 🚦 اعمال قفل‌ها (فیلتر پیام‌ها) ==================
@bot.message_handler(content_types=['text','photo','video','document','audio','voice','sticker','animation'])
def enforce_all(m):
    if is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id): return
    txt = m.text or ""

    # قفل کل گروه
    if group_lock.get(m.chat.id):
        try:
            bot.delete_message(m.chat.id, m.message_id)
        except:
            pass
        return

    # سایر قفل‌ها
    try:
        if locks["links"].get(m.chat.id) and any(x in txt for x in ["http://","https://","t.me"]):
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

# ====== پایان مرحله ۱ (بدون اجرای ربات). اجرای نهایی در مرحله ۲ اضافه می‌شود. ======import json
from telebot import types

# ================== 🗂 فایل داده ==================
DATA_FILE = "data.json"

# اگر فایل وجود نداشت، بساز
if not os.path.exists(DATA_FILE):
    data = {"admins": [], "sudos": list(sudo_ids), "groups": {}, "welcome": {}}
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ================== 🎉 خوشامدگویی ==================
@bot.message_handler(content_types=["new_chat_members"])
def welcome_new_member(m):
    data = load_data()
    group_settings = data["welcome"].get(str(m.chat.id), {"enabled": True, "type": "text", "content": "👋 خوش آمدی {name} به گروه!"})
    if not group_settings.get("enabled", True):
        return

    name = m.new_chat_members[0].first_name
    text = group_settings["content"].replace("{name}", name)

    if group_settings["type"] == "text":
        bot.send_message(m.chat.id, text)
    elif group_settings["type"] == "photo":
        try:
            bot.send_photo(m.chat.id, group_settings["file_id"], caption=text)
        except:
            bot.send_message(m.chat.id, text)

@bot.message_handler(func=lambda m: cmd_text(m) in ["خوشامد روشن", "خوشامد خاموش"])
def toggle_welcome(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    data = load_data()
    group = str(m.chat.id)
    enabled = (cmd_text(m) == "خوشامد روشن")
    data["welcome"][group] = data["welcome"].get(group, {"enabled": True, "type": "text", "content": "👋 خوش آمدی {name} به گروه!"})
    data["welcome"][group]["enabled"] = enabled
    save_data(data)
    bot.reply_to(m, "✅ خوشامد فعال شد" if enabled else "🚫 خوشامد غیرفعال شد")

@bot.message_handler(func=lambda m: cmd_text(m) == "تنظیم خوشامد متن" and m.reply_to_message)
def set_welcome_text(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    data = load_data()
    group = str(m.chat.id)
    text = m.reply_to_message.text or ""
    data["welcome"][group] = {"enabled": True, "type": "text", "content": text}
    save_data(data)
    bot.reply_to(m, "✅ متن خوشامد تنظیم شد")

@bot.message_handler(func=lambda m: cmd_text(m) == "تنظیم خوشامد عکس" and m.reply_to_message and m.reply_to_message.photo)
def set_welcome_photo(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    data = load_data()
    group = str(m.chat.id)
    file_id = m.reply_to_message.photo[-1].file_id
    caption = m.reply_to_message.caption or "👋 خوش آمدی {name}"
    data["welcome"][group] = {"enabled": True, "type": "photo", "file_id": file_id, "content": caption}
    save_data(data)
    bot.reply_to(m, "🖼 خوشامد تصویری تنظیم شد")

# ================== 📎 لینک گروه ==================
@bot.message_handler(func=lambda m: cmd_text(m) == "لینک")
def get_link(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    try:
        link = bot.export_chat_invite_link(m.chat.id)
        bot.reply_to(m, f"🔗 لینک گروه:\n{link}")
    except:
        bot.reply_to(m, "❗ نتونستم لینک گروه رو بگیرم. مطمئن شو من ادمینم و دسترسی دارم.")

# ================== ✉️ ارسال همگانی ==================
waiting_for_broadcast = {}

@bot.message_handler(func=lambda m: cmd_text(m) == "ارسال همگانی")
def ask_broadcast(m):
    if not is_sudo(m.from_user.id): return
    waiting_for_broadcast[m.from_user.id] = True
    bot.reply_to(m, "📝 لطفاً متن پیام همگانی رو بفرست:")

@bot.message_handler(func=lambda m: m.from_user.id in waiting_for_broadcast)
def send_broadcast(m):
    if not is_sudo(m.from_user.id): return
    text = m.text
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

# ================== 👮 مدیریت مدیران و سودو ==================
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="افزودن مدیر")
def add_admin(m):
    if not is_sudo(m.from_user.id): return
    data = load_data()
    uid = m.reply_to_message.from_user.id
    if uid not in data["admins"]:
        data["admins"].append(uid)
        save_data(data)
        bot.reply_to(m, "👮 مدیر جدید اضافه شد.")
    else:
        bot.reply_to(m, "❗ این کاربر قبلاً مدیر بود.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف مدیر")
def del_admin(m):
    if not is_sudo(m.from_user.id): return
    data = load_data()
    uid = m.reply_to_message.from_user.id
    if uid in data["admins"]:
        data["admins"].remove(uid)
        save_data(data)
        bot.reply_to(m, "🚫 مدیر حذف شد.")
    else:
        bot.reply_to(m, "❗ این کاربر مدیر نیست.")

@bot.message_handler(func=lambda m: cmd_text(m)=="لیست مدیران")
def list_admins(m):
    if not is_sudo(m.from_user.id): return
    data = load_data()
    if not data["admins"]:
        return bot.reply_to(m, "❗ هیچ مدیری ثبت نشده.")
    txt = "\n".join([f"▪️ {uid}" for uid in data["admins"]])
    bot.reply_to(m, "👮 لیست مدیران:\n"+txt)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="افزودن سودو")
def add_sudo(m):
    if not is_sudo(m.from_user.id): return
    data = load_data()
    uid = m.reply_to_message.from_user.id
    if uid not in data["sudos"]:
        data["sudos"].append(uid)
        save_data(data)
        sudo_ids.add(uid)
        bot.reply_to(m, "⚡ سودو جدید اضافه شد.")
    else:
        bot.reply_to(m, "❗ این کاربر سودو است.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف سودو")
def del_sudo(m):
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

@bot.message_handler(func=lambda m: cmd_text(m)=="لیست سودو")
def list_sudos(m):
    if not is_sudo(m.from_user.id): return
    data = load_data()
    if not data["sudos"]:
        return bot.reply_to(m, "❗ سودویی ثبت نشده.")
    txt = "\n".join([f"▪️ {uid}" for uid in data["sudos"]])
    bot.reply_to(m, "⚡ لیست سودوها:\n"+txt)

# ================== 🧭 پنل مدیریت (کیبورد اینلاین) ==================
@bot.message_handler(func=lambda m: cmd_text(m)=="پنل")
def panel_menu(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎉 خوشامد", callback_data="panel_welcome"),
               types.InlineKeyboardButton("📎 لینک", callback_data="panel_link"))
    markup.add(types.InlineKeyboar
