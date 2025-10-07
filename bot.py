# -*- coding: utf-8 -*-
import os, random
from datetime import datetime
import pytz
import telebot

# ================== ⚙️ تنظیمات ==================
TOKEN   = os.environ.get("BOT_TOKEN") or "توکن_ربات_اینجا"
SUDO_ID = int(os.environ.get("SUDO_ID", "آیدی_عددیت_اینجا"))

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
sudo_ids = {SUDO_ID}

# ================== 🧩 توابع کمکی ==================
def is_sudo(uid): return uid in sudo_ids
def is_admin(chat_id, user_id):
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator","creator")
    except:
        return False

def cmd_text(m): return (getattr(m,"text",None) or "").strip()

# ================== 💬 دستورات عمومی ==================
@bot.message_handler(func=lambda m: cmd_text(m)=="ساعت")
def cmd_time(m):
    now_utc=datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
    now_teh=datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
    bot.reply_to(m,f"⏰ UTC: {now_utc}\n🕓 تهران: {now_teh}")

@bot.message_handler(func=lambda m: cmd_text(m)=="آمار")
def cmd_stats(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    try:
        count = bot.get_chat_member_count(m.chat.id)
    except:
        count = "نامشخص"
    bot.reply_to(m,f"📊 اعضای گروه: {count}")

@bot.message_handler(func=lambda m: cmd_text(m)=="ایدی")
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

# ================== 👑 پاسخ سودو ==================
SUDO_RESPONSES = [
    "جونم قربان 😎",
    "در خدمتم ✌️",
    "ربات آماده‌ست 🚀",
    "چه خبر رئیس؟ 🤖"
]

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="ربات")
def cmd_sudo(m):
    bot.reply_to(m, random.choice(SUDO_RESPONSES))# ================== 🔒 قفل‌ها ==================
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

# --- بن
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="بن")
def ban(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    if (msg := protect_user(m.chat.id, uid)): return bot.reply_to(m, msg)
    try:
        bot.ban_chat_member(m.chat.id, uid)
        banned.setdefault(m.chat.id, set()).add(uid)
        bot.reply_to(m, "🚫 کاربر بن شد")
    except: bot.reply_to(m, "❗ خطا در بن")

# --- حذف بن
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف بن")
def unban(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    try:
        bot.unban_chat_member(m.chat.id, uid)
        banned.get(m.chat.id,set()).discard(uid)
        bot.reply_to(m, "✅ بن حذف شد")
    except: bot.reply_to(m, "❗ خطا در حذف بن")

# --- سکوت
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="سکوت")
def mute(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    if (msg := protect_user(m.chat.id, uid)): return bot.reply_to(m, msg)
    try:
        bot.restrict_chat_member(m.chat.id, uid, can_send_messages=False)
        muted.setdefault(m.chat.id, set()).add(uid)
        bot.reply_to(m, "🔕 کاربر در سکوت قرار گرفت")
    except: bot.reply_to(m, "❗ خطا در سکوت")

# --- حذف سکوت
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف سکوت")
def unmute(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    try:
        bot.restrict_chat_member(m.chat.id, uid,
            can_send_messages=True, can_send_media_messages=True,
            can_send_other_messages=True, can_add_web_page_previews=True)
        muted.get(m.chat.id,set()).discard(uid)
        bot.reply_to(m, "🔊 سکوت حذف شد")
    except: bot.reply_to(m, "❗ خطا در حذف سکوت")

# --- اخطار
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="اخطار")
def warn(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    if (msg := protect_user(m.chat.id, uid)): return bot.reply_to(m, msg)
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

# --- حذف اخطار
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف اخطار")
def reset_warn(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    warnings.get(m.chat.id, {}).pop(uid, None)
    bot.reply_to(m, "✅ اخطارها حذف شد")

# ================== 🧹 پاکسازی ==================
@bot.message_handler(func=lambda m: (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)) and cmd_text(m)=="پاکسازی")
def clear_all(m):
    deleted = 0
    try:
        for i in range(1, 201):
            bot.delete_message(m.chat.id, m.message_id - i)
            deleted += 1
    except: 
        pass
    bot.reply_to(m, f"🧹 {deleted} پیام پاک شد")

@bot.message_handler(func=lambda m: (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)) and cmd_text(m).startswith("حذف "))
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

# ================== 🚦 اجرای قفل‌ها ==================
@bot.message_handler(content_types=['text','photo','video','document','audio','voice','sticker','animation'])
def enforce_all(m):
    if is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id): return
    txt = m.text or ""
    # قفل کل گروه
    if group_lock.get(m.chat.id):
        try: bot.delete_message(m.chat.id, m.message_id)
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
    except: passimport json

# ================== 📁 فایل ذخیره داده‌ها ==================
DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"welcome": {}, "admins": {}, "sudo_list": []}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"welcome": {}, "admins": {}, "sudo_list": []}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

# ================== 🌸 خوشامدگویی ==================
@bot.message_handler(func=lambda m: cmd_text(m)=="خوشامد روشن")
def welcome_on(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    data["welcome"][str(m.chat.id)] = {"enabled": True, "text": "🌸 خوش اومدی [name]!", "photo": None}
    save_data()
    bot.reply_to(m, "✅ خوشامد فعال شد.")

@bot.message_handler(func=lambda m: cmd_text(m)=="خوشامد خاموش")
def welcome_off(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    data["welcome"][str(m.chat.id)] = {"enabled": False}
    save_data()
    bot.reply_to(m, "❌ خوشامد خاموش شد.")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("تنظیم متن خوشامد "))
def set_welcome_text(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    txt = m.text.replace("تنظیم متن خوشامد ", "", 1)
    data["welcome"].setdefault(str(m.chat.id), {})["text"] = txt
    save_data()
    bot.reply_to(m, "📝 متن خوشامد تنظیم شد.")

@bot.message_handler(content_types=['photo'])
def set_welcome_photo(m):
    if m.caption == "تنظیم عکس خوشامد" and (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)):
        fid = m.photo[-1].file_id
        data["welcome"].setdefault(str(m.chat.id), {})["photo"] = fid
        save_data()
        bot.reply_to(m, "🖼 عکس خوشامد تنظیم شد.")

@bot.message_handler(content_types=['new_chat_members'])
def welcome_new(m):
    conf = data["welcome"].get(str(m.chat.id), {})
    if not conf.get("enabled"): return
    for user in m.new_chat_members:
        name = user.first_name
        txt = conf.get("text","🌸 خوش اومدی [name]!").replace("[name]", name)
        if conf.get("photo"):
            bot.send_photo(m.chat.id, conf["photo"], caption=txt)
        else:
            bot.send_message(m.chat.id, txt)

# ================== 📬 ارسال همگانی (فقط سودو) ==================
broadcast_text = {}

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="ارسال همگانی")
def ask_broadcast(m):
    broadcast_text[m.from_user.id] = True
    bot.reply_to(m, "📝 لطفا متن مورد نظر برای ارسال همگانی را ارسال کنید:")

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and m.from_user.id in broadcast_text)
def do_broadcast(m):
    del broadcast_text[m.from_user.id]
    text = m.text
    sent = 0
    for chat_id in data["welcome"].keys():
        try:
            bot.send_message(int(chat_id), text)
            sent += 1
        except: 
            pass
    bot.reply_to(m, f"📨 پیام به {sent} گروه ارسال شد.")

# ================== 👑 مدیریت مدیران و سودو ==================
@bot.message_handler(func=lambda m: cmd_text(m).startswith("افزودن مدیر "))
def add_admin(m):
    if not is_sudo(m.from_user.id): return
    uid = int(cmd_text(m).split()[2]) if len(cmd_text(m).split()) > 2 else None
    if not uid: return bot.reply_to(m, "❗ فرمت: افزودن مدیر 12345")
    data["admins"].setdefault(str(m.chat.id), set()).add(uid)
    save_data()
    bot.reply_to(m, f"✅ مدیر {uid} افزوده شد.")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("حذف مدیر "))
def del_admin(m):
    if not is_sudo(m.from_user.id): return
    uid = int(cmd_text(m).split()[2]) if len(cmd_text(m).split()) > 2 else None
    data["admins"].get(str(m.chat.id), set()).discard(uid)
    save_data()
    bot.reply_to(m, "❌ مدیر حذف شد.")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("افزودن سودو "))
def add_sudo(m):
    if not is_sudo(m.from_user.id): return
    uid = int(cmd_text(m).split()[2])
    data["sudo_list"].append(uid)
    save_data()
    sudo_ids.add(uid)
    bot.reply_to(m, f"👑 کاربر {uid} به عنوان سودو افزوده شد.")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("حذف سودو "))
def del_sudo(m):
    if not is_sudo(m.from_user.id): return
    uid = int(cmd_text(m).split()[2])
    if uid in data["sudo_list"]:
        data["sudo_list"].remove(uid)
        sudo_ids.discard(uid)
        save_data()
    bot.reply_to(m, "❌ سودو حذف شد.")

# ================== 📚 راهنما ==================
@bot.message_handler(func=lambda m: cmd_text(m) in ["راهنما","help","دستورات"])
def help_menu(m):
    txt = """
📘 <b>راهنمای ربات مدیریت گروه</b>

🕓 <b>عمومی</b>
• ساعت
• آمار
• ایدی

😂 <b>تفریحی</b>
• جوک / فال

🔒 <b>قفل‌ها</b>
• قفل لینک / عکس / گیف / ویدیو ...
• قفل گروه / باز کردن گروه

👮‍♂️ <b>مدیریتی</b>
• بن / حذف بن
• سکوت / حذف سکوت
• اخطار / حذف اخطار
• پاکسازی / حذف 10

🌸 <b>خوشامدگویی</b>
• خوشامد روشن / خاموش
• تنظیم متن خوشامد [متن]
• ارسال عکس با کپشن "تنظیم عکس خوشامد"

📬 <b>سودو</b>
• ارسال همگانی
• افزودن مدیر [ایدی]
• حذف مدیر [ایدی]
• افزودن سودو [ایدی]
• حذف سودو [ایدی]
"""
    bot.reply_to(m, txt, parse_mode="HTML")

# ================== 🚀 اجرای ربات ==================
print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True, timeout=30)
